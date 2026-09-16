# AWS構成案

mogumiを外部公開するための、AWS上の構成案。詳細な検討経緯は [Issue #4](https://github.com/Kedama515/mogumi/issues/4) を参照。

## 前提・方針

- 公開は「フェーズ1: 限定公開(知人向け)」→「フェーズ2: 本格公開(不特定多数サインアップ、[Issue #47](https://github.com/Kedama515/mogumi/issues/47))」の2段階で進める
- 基盤はAWSに統一する。理由は主に、フェーズ間で基盤ごと乗り換える移行リスクを避けられること、Claude呼び出しをAmazon Bedrock経由にすることでAPIキー管理が不要になること、ログ管理([Issue #48](https://github.com/Kedama515/mogumi/issues/48))もCloudWatch Logsでカバーできること
- 予算目安: 月$30程度(EC2代+Bedrock従量課金込み)。AWS無料利用枠は使用済みの前提でコストを見積もる
- Claude呼び出しは `Anthropic` SDKの直接呼び出しから、Amazon Bedrock経由(`AnthropicBedrock`クライアント等)に切り替える。実装時は最新のドキュメントでモデルID・SDK仕様を確認すること(記憶に頼らない)
- リソースの構築はTerraform(IaC)で行う。手動コンソール操作は避け、タグ運用ルールの徹底やフェーズ2への構成変更を再現性を持って進められるようにする

## フェーズ1: 限定公開(知人向け)

```mermaid
flowchart LR
    User[知人のブラウザ] -->|HTTPS| ALB_OR_DIRECT[EC2: nginx]
    subgraph EC2インスタンス [EC2 (t4g系, ARM)]
        nginx[nginx] --> frontend[frontend静的ビルド]
        nginx --> backend[uvicorn: FastAPI]
        backend --> sqlite[(SQLite on EBS)]
    end
    backend -->|IAMロール経由| Bedrock[Amazon Bedrock: Claude]
    backend -->|ログ出力| CloudWatch[CloudWatch Logs]
```

### 構成要素

| 要素 | 内容 |
|---|---|
| コンピュート | EC2インスタンス1台(t4g.micro〜t4g.small、ARM/Graviton。Python・Node.jsともARM対応ビルドあり) |
| ストレージ | EBSボリューム(gp3、10〜20GB程度)に`mogumi.db`(SQLite)を配置 |
| Webサーバー | nginxでリバースプロキシ。`/api`はuvicorn(FastAPI)へ、それ以外は`frontend`のビルド済み静的ファイルを配信 |
| HTTPS | Let's Encrypt(certbot)でnginxに証明書を設定。独自ドメインを使う場合はRoute 53で管理してもよいし、レジストラのDNSのままでも可 |
| Claude呼び出し | EC2インスタンスにBedrock呼び出し用のIAMロールをアタッチ(`bedrock:InvokeModel`等、最小権限に絞る)。`ANTHROPIC_API_KEY`のようなシークレットをサーバー上に置く必要がなくなる |
| ログ | アプリのログを`logging`モジュール経由でCloudWatch Logsに送る(#48と合わせて実装) |
| ユーザー管理 | 現状どおり`scripts/create_user.py`で作成、または#46のサインアップ機能を使う |

### なぜこの構成か

- SQLiteはファイルベースのDBなので、永続化されたディスク(EBS)を持つ通常のEC2インスタンスと相性が良い。コンテナ/サーバーレス(ECS Fargate, Lambda等)は起動のたびにファイルシステムがリセットされる構成が多く、素直に載せるとデータが消えるためフェーズ1では避ける
- EC2 1台+nginxという最小構成にすることで、知人数人向けの検証段階に見合った運用コスト・金銭コストに抑える
- IAMロールでのBedrockアクセスは、EC2インスタンス自体が既にAWSの権限管理下にあるため、追加のシークレット管理の手間なく実現できる

### 概算コスト(フェーズ1、無料利用枠なし)

| 項目 | 目安 |
|---|---|
| EC2(t4g.micro、24時間稼働) | 月 $5〜8 |
| EBS(gp3 20GB) | 月 $1〜2 |
| Bedrock(Claude、知人数人の利用量) | 月 $1〜5程度(要実測) |
| データ転送量(小規模なら無料枠内に収まる想定) | ほぼ$0 |
| **合計目安** | **月 $10〜20程度**(予算上限$30に収まる) |

## フェーズ2: 本格公開(不特定多数サインアップ、#47と連動)

フェーズ1のEC2インスタンスは維持しつつ、以下を段階的に足していくイメージ。基盤を乗り換えるのではなく、同じAWSアカウント内で拡張する。

```mermaid
flowchart LR
    User[不特定多数のブラウザ] -->|HTTPS| ALB[Application Load Balancer]
    ALB --> EC2a[EC2 / ECSタスク #1]
    ALB --> EC2b[EC2 / ECSタスク #2]
    EC2a --> RDS[(RDS PostgreSQL)]
    EC2b --> RDS
    EC2a -->|IAMロール経由| Bedrock[Amazon Bedrock: Claude]
    EC2a -->|ログ出力| CloudWatch[CloudWatch Logs]
    EC2a -->|レート制限用| Cache[(ElastiCache or DB上のカウンタ)]
```

### フェーズ1からの主な変更点

| 項目 | フェーズ1 | フェーズ2 |
|---|---|---|
| DB | EC2上のSQLite | RDS PostgreSQL(複数ユーザーの同時書き込みに対応) |
| コンピュート | EC2 1台 | ALB配下でEC2複数台 or ECS Fargateでスケール(必要になってから) |
| HTTPS証明書 | Let's Encrypt(certbot) | ACMでALBのHTTPSリスナーに証明書を割り当て(certbotの更新運用が不要になる) |
| DNS | レジストラのDNSのまま、または未取得 | 独自ドメインを取得する場合はRoute 53で管理し、エイリアスレコードでALBを指す(#51) |
| レート制限 | なし | プラン別(`users.plan`)の上限をアプリ側で実装。カウンタの保存先はRDSか、必要ならElastiCache(Redis) |
| 監視 | 最低限のCloudWatch Logs | CloudWatchアラーム(エラー率・レイテンシ・コスト)を追加 |
| その他 | - | #47の各項目(利用規約・パスワードリセット・メール確認等)に対応 |

このフェーズへの移行は、実際に不特定多数向けサインアップを始めるタイミングで着手する(現時点では設計メモのみ)。

## セキュリティ設計メモ

- EC2のセキュリティグループは、80/443(HTTP/HTTPS)のみを外部公開し、SSH(22番)は自分のIPからのみに制限する
- IAMロールはBedrock呼び出しに必要な権限(`bedrock:InvokeModel`など)のみを付与し、他のAWSサービスへの権限は持たせない(最小権限の原則)
- `MOGUMI_SECRET_KEY`(JWT署名鍵)は引き続き環境変数で管理し、AWS Systems Manager Parameter StoreやSecrets Managerへの格納も検討する(フェーズ2で本格検討)

## アカウント初期設定チェックリスト

Organizations/メンバーアカウント作成の前後で対応する、アカウントレベルの運用設定。

- [ ] root MFAの設定(対応済み)
- [ ] AWS Budgetsで予算アラートを設定する → [Issue #53](https://github.com/Kedama515/mogumi/issues/53)
- [ ] CloudTrailが有効化されているか確認する → [Issue #54](https://github.com/Kedama515/mogumi/issues/54)
- [x] IAM Identity Centerのホームリージョンを決定する(`ap-northeast-1`) → [Issue #55](https://github.com/Kedama515/mogumi/issues/55)
- [ ] AWSアカウントの代替連絡先を設定する → [Issue #56](https://github.com/Kedama515/mogumi/issues/56)
- [ ] GuardDuty(脅威検知)を有効化する → [Issue #57](https://github.com/Kedama515/mogumi/issues/57)
- サポートプランはBasic(無料)のままでよい、AWS Configは個人開発の規模ではオーバースペックなので現時点では対応しない

## アカウント構成

- 既存のAWSアカウントをAWS Organizationsの管理アカウントとし、その配下に「mogumi」専用のメンバーアカウントを新規作成する(コストの切り分け・影響範囲の隔離のため)
- メンバーアカウント作成時のrootメールアドレスは、プラスアドレス方式(例: `本来のアドレス+mogumi@gmail.com`)で発行する
- メンバーアカウント作成時のIAMロール名はデフォルトの`OrganizationAccountAccessRole`のまま変更しない(命名を変える実質的なセキュリティ上のメリットはなく、AWS公式ドキュメントとの整合性を優先する)
- 日常的なアクセスはIAM Identity Centerで一元化する(管理アカウント側で有効化し、権限セットをmogumiアカウントに割り当てる)。`OrganizationAccountAccessRole`は管理アカウントからの緊急時アクセス経路という位置づけ
- IAM Identity Centerのホームリージョンは`ap-northeast-1`(東京)とする(決定: 2026-09-16、[Issue #55](https://github.com/Kedama515/mogumi/issues/55))

### タグ運用ルール

mogumiアカウント自体、および中で作成する全リソース(EC2・EBS・RDS等)に、以下のタグを標準で付与する。コスト管理(月$30の予算をCost Explorerで正確に追う)とリソース整理のため。

| キー | 値の例 | 備考 |
|---|---|---|
| `Project` | `mogumi` | 固定 |
| `Environment` | `personal` | フェーズ2で本格公開したら`production`等に更新する |
| `Owner` | (本人の名前 or ハンドル名) | |

キーは大文字始まりで統一する(`project`のような小文字表記は別タグとして扱われてしまうため)。

### 命名規則

リソース名にも`mogumi`プレフィックスを付け、フェーズ(環境)による違いが名前だけで分かるようにする。

| スコープ | パターン | 例 |
|---|---|---|
| アカウント全体対象(フェーズ問わず一つだけ存在するもの) | `mogumi-all-<resource-type>` | `mogumi-all-budget` |
| フェーズ固有のリソース | `mogumi-<environment>-<resource-type>[-<qualifier>]` | `mogumi-personal-ec2-app`, `mogumi-personal-sg-web` |
| IAM Identity Center権限セット等、フェーズの概念がないアクセス制御系 | `mogumi-<用途>` | `mogumi-admin` |

`environment`の値はタグ運用ルールの`Environment`タグと揃える(`personal` → フェーズ2で`production`)。「両方の環境が対象」であることを明示したい場合は環境名を省略せず`all`と書く(名前から意図的に省いたのか書き忘れたのか区別がつくように)。

IAM Identity CenterのGroupとPermission setのように、同じ用途で名前が衝突しうる場合はリソース種別をサフィックスで明示する(すべて小文字、ハイフン区切りで統一)。例: Group `mogumi-admin-group` / Permission set `mogumi-admin`。

## 未確定・今後決めること

- 独自ドメインを取得するかどうか(取得する場合はRoute 53 or 外部レジストラ+DNS設定) → [Issue #51](https://github.com/Kedama515/mogumi/issues/51)
- フェーズ1のインスタンスサイズ(t4g.micro / t4g.small)は実際の負荷を見ながら調整 → [Issue #52](https://github.com/Kedama515/mogumi/issues/52)
- レート制限の実装方式の詳細 → [Issue #47](https://github.com/Kedama515/mogumi/issues/47)

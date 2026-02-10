# azure-spotvm-starts-when-stopped

Azure Spot VM が停止・割り当て解除された際に、自動で再起動する Azure Functions アプリケーションです。

Azure Spot VM はコスト効率に優れる一方、Azure の容量需要に応じていつでもエビクト（強制停止）される可能性があります。本アプリケーションは Timer Trigger で VM の状態を毎分監視し、停止を検知すると自動的に起動を試みます。

## 仕組み

1. Azure Functions の Timer Trigger が **60秒ごと** に実行される
2. 指定された VM の電源状態 (`PowerState`) を Azure API で取得する
3. `VM running` 以外の状態（`VM deallocated` 等）を検知した場合、`begin_start` で VM の起動を開始する

## 前提条件

- Python 3.9 以上
- Azure サブスクリプション
- [Azure Functions Core Tools](https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-run-local) v4
- [Azure CLI](https://learn.microsoft.com/ja-jp/cli/azure/install-azure-cli)

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/shigechika/azure-spotvm-starts-when-stopped.git
cd azure-spotvm-starts-when-stopped
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

以下の環境変数を設定してください。

| 変数名 | 説明 | 例 |
|---|---|---|
| `AZURE_SUBSCRIPTION_ID` | Azure サブスクリプション ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `RESOURCE_GROUP_NAME` | 対象 VM が所属するリソースグループ名 | `my-resource-group` |
| `VM_NAME` | 監視対象の VM 名 | `my-spot-vm` |

ローカル実行の場合は `local.settings.json` を作成します。

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AZURE_SUBSCRIPTION_ID": "<your-subscription-id>",
    "RESOURCE_GROUP_NAME": "<your-resource-group>",
    "VM_NAME": "<your-vm-name>"
  }
}
```

### 4. ローカルでの実行

```bash
func start
```

## Azure へのデプロイ

### 1. Function App の作成

```bash
az functionapp create \
  --resource-group <your-resource-group> \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name <your-function-app-name> \
  --storage-account <your-storage-account>
```

### 2. マネージド ID の有効化と権限付与

Function App がVMを操作するために、システム割り当てマネージド ID を有効にし、対象 VM に対する **仮想マシン共同作成者** ロールを付与します。

```bash
# マネージド ID の有効化
az functionapp identity assign \
  --name <your-function-app-name> \
  --resource-group <your-resource-group>

# ロールの割り当て（出力された principalId を使用）
az role assignment create \
  --assignee <principal-id> \
  --role "Virtual Machine Contributor" \
  --scope /subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Compute/virtualMachines/<vm-name>
```

### 3. アプリケーション設定の追加

```bash
az functionapp config appsettings set \
  --name <your-function-app-name> \
  --resource-group <your-resource-group> \
  --settings \
    AZURE_SUBSCRIPTION_ID=<your-subscription-id> \
    RESOURCE_GROUP_NAME=<your-resource-group> \
    VM_NAME=<your-vm-name>
```

### 4. デプロイ

```bash
func azure functionapp publish <your-function-app-name>
```

## プロジェクト構成

```
.
├── function_app.py      # メインのアプリケーションコード
├── host.json            # Azure Functions ホスト設定
├── requirements.txt     # Python 依存パッケージ
├── LICENSE              # Apache License 2.0
└── README.md
```

## ライセンス

[Apache License 2.0](LICENSE)

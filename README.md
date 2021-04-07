# Ansible collection for Yamaha RTX/NVR/FWX/vRX series

このリポジトリはヤマハネットワーク製品向けAnsibleモジュールリポジトリです。

## Modules
- rtx_command.py-ヤマハ機器(RTX/NVR/FWX/vRX)の実行系コマンドを実行するためのモジュール
- rtx_config.py-ヤマハ機器(RTX/NVR/FWX/vRX)の設定系コマンドを実行するためのモジュール

### Documents
インストール手順やモジュールの詳細は以下をご覧ください。

[RTpro](http://www.rtpro.yamaha.co.jp/RT/docs/ansible/index.html) : ヤマハネットワーク製品技術情報ページ

[Ansible Galaxy](https://galaxy.ansible.com/yamaha_network/rtx) : Ansible Galaxyヤマハコレクションページ

## Requirements
- Ansible 2.10

### Supported connections
Yamaha rtx collectionは``network_cli``を用いた接続をサポートします。

## Structure
本レポジトリの構成を以下に示します。
```
master
├─inventory                  #ターゲットのIPや変数を記載
├─README.txt                 #本ドキュメント
├─ansible_collections        #本ディレクトリ以下がansible-galaxyにまとめてtar形式で公開されます
│  └─yamaha_network
|     └─rtx
│        └─galaxy.yml　　　 　#ansible-galaxy公開用のファイル
│        └─README.md         #ansible-galaxy用のREADME
│        └─plugins　　　　　　#各種プラグインとモジュール本体
│　　       └─action
│  　　     └─cliconf
│    　　   └─module_utils
│  　　     └─modules
│    　　   └─terminal
├─playbook     　 　          #サンプルプレイブック
```

<br>

## Parameters

### rtx_command
| Parameters | options | description |
|:---:|:---:|---|
| commands |-| 非特権モードで実行可能な各コマンドを実行する |
| interval |-| コマンドをリトライするために指定した秒数待つ |
| match | wait_for | 設定したすべての条件が満たされたときにタスクの実行を再開する |
|-| any | いずれかの条件が満たされたときタスクの実行を再開する |
| wait_for |-| コマンドの実行結果が満たすべき条件のリストを設定する |
| retries |-| 指定した回数だけリトライする(デフォルトは10回) |

### rtx_config
| Parameters | options | description |
|:---:|:---:|---|
| lines |-| 特権モードで実行可能な各コマンドを実行できる |
| after |-| コンフィグの変更を行なった後に設定するリストを設定する |
| before |-| コンフィグの変更を行う前に設定するコマンドのリストを設定する |
| backup |-| running-configのバックアップを行うかを設定する |
| backup_options | dir_path | backupがyesの時に参照され、ファイルが作成される場所を設定する |
|-| filemame | backupがyesの時に参照され、作成される名前を設定する |
| diff_against | intended | ansible-playbook --diffとすることでdiffを作成する際にintendedコンフィグと比較する |
|-| running | ansible-playbook --diffとすることでdiffを作成する際にrunningコンフィグと比較する |
| intended_config |-| diff_againstオプションにintendedを設定した場合に比較を行うコンフィグを設定する |
| diff_ignores_lines |-| 差分を無視する(diff表示に出力されない) |
| match | line | コマンド1行毎にその設定が存在するか比較して設定を行う(デフォルト値) |
|-| strict | 設定されている位置(行数)が異なる場合はコマンド設定を行う |
|-| exact | 設定が完全に一致している場合以外はコマンド設定を行う |
|-| none | 比較をせずに設定を行う |
| parents |-| linesオプションで設定したコンフィグを実行する階層のリストを設定する。pp selectコマンドなどコンフィグ内で1段下がる手前で設定する。 |
| running_config |-| 稼働中のコンフィグを参照する代わりに比較対象とするコンフィグを設定する |
| save_when | always | 常に保存する |
|-| never | 常に保存しない |
|-| changed | タスク実行により変更がある時に保存する |
| src |-| 設定対象のコンフィグを記載したパスを設定する |

## Copyright
Copyright (C) Yamaha Corporation. All Rights Reserved.
## License
### GPL V3
See the [LICENSE](ansible_collections/yamaha_network/rtx/LICENSE) file.
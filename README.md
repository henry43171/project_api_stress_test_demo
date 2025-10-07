# API Stress Test Simulator

## 專案簡介
- 本專案用於模擬不同的 API 壓力測試情境
- API流程有三步驟，進入網頁、取得表單、送出表單
- 支援高併發測試（High Concurrency）及長時間測試（Long Duration），來模擬不同流程
- 自動生成測試報告與日誌
- 各項功能可透過參數來調整測試內容

## 目錄結構（簡略）
```
.
├── app/                # API Server
├── config_example/     # 範例config
├── core/               # 核心測試邏輯
├── fake_data/          # 假資料生成
├── results/            # 測試結果與日誌
├── test_tool/          # 壓力測試腳本
└── utils/              # 工具函式（報告生成、假資料生成等）
```

## 快速開始
### 環境需求
1. 安裝 Python 3.11+
2. 安裝需求套件
    
    `pip install flask flasgger requests matplotlib`


### 配置說明
- core.json：核心測試參數，只有API網址
- server_config.json：API 伺服器配置，可調整人數負載的上下限、API成功率
- fake_data.json：生成假資料所用的參數，這些假資料是專門為此API設計，可以決定要生成的資料數量
- high_concurrency.json：高併發測試參數，可決定每一批測試的數量
- long_duration.json：長時間測試參數，可決定測試總時間、單位時間、人數、人數峰值等等

### 模組功能概覽
- app/app_server.py:API服務
- utils/fake_data_generetor.py：假資料生成工具
- core/api_test_core.py：API 壓力測試核心邏輯
- test_tool/high_concurrency.py：高併發測試腳本
- test_tool/long_duration.py：長時間測試腳本
- utils/generate_report.py：假資料生成工具

### 使用方法

1. 啟動測試服務

    `python -m app.app_server`

2. 生成假資料
   
    利用假資料生成工具生成假資料，確保後續測試結果一致，後續的高併發/長時間測試都用使用到生成後的資料。
   
    `python -m utils.generate_report --high_concurrency`
   

3. 高併發測試

    `python -m test_tool.high_concurrency`

3. 長時間測試

    `python -m test_tool.long_duration`

4. 視覺化報表

    生成高併發測試報表
    
    `python -m utils.generate_report --high_concurrency`
    
    生成長時間測試報表
    
    `python -m utils.generate_report --long_duration`



### 測試報告與結果
- results/logs/：測試過程的原始日誌
- results/summary/：測試結果彙總報告
- utils/generate_report.py：可生成圖表，會是柱狀圖和折線圖的整合圖表

## 未來擴展
- 整合測試與圖表呈現
- 支援不同模式的測試，例如在不同API操作中加入權重模擬用戶行為等等

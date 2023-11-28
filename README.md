# HengTrader ![image](https://img.shields.io/badge/HengTrader-0.000001%2B-blue)
> A project for algorithmic trading of cryptocurrencies.
> Possibly the only profit strategy freely available on the internet.
> 可能是全网唯一的，免费公开的盈利策略。

---
# 公告：最后的策略更新

经过两个月的开发和探索，我们成功地找到了一种利用机器学习进行加密货币短线交易的算法，并在随后的两个月里得到了较高的超额收益。截至2023-11-28，我们的 SpotBot 已经为账户赢得了50%的收益，如果您感兴趣算法交易的话，这很可能是全网唯一将实际盈利的策略完整公开的代码库。

我们取得的成果包括：
1. 基于我们的因子库，我们构建了两个不同的 Bot：
    - **SpotBot**：进行 Spot 交易，只允许做多。在首个月取得超过30%的收益。
    - **FutureBot**：进行 Future 交易，通过对冲获得绝对收益。允许杠杆和做空，与 BTC，ETH 相关性低于0.3。在首个月取得20%的绝对收益。

2. 我们探索并实践了几种利用数据科学方法进行交易的思路，包括：
    - 利用筛选机制过滤噪声时间段
    - 利用池化方法降低数据噪声，避免过拟合
    - 使用 Z_score 和差分，榨取因子的完全信息。
    - ...
随着技术的深入和团队的扩大，更多有价值的数据处理方式，与更加有效的因子被发现。目前，这个项目受到了更多关注，也融合了许多人的智慧。由于利益相关者的增加，继续公开我们的全部策略和因子是不合适的。
遗憾的是，今后我们不会继续更新完整的策略。但是我们仍然会继续更新相关的数据观察，教程和代码示例。
如果您对我们的工作感兴趣，欢迎探讨和学习！

感谢您的支持，
Henry Miao.

# Introduction 
这个仓库包含了我对加密货币自动化交易的探索过程。它以一个简单的均值回归为起点，最终得到了一个基于机器学习的策略。这个项目中，我开发了自己的第一个实盘盈利的交易算法，并以此为基础设计了几个变体。

这些策略都是分钟频的，而且都基于量价数据的挖掘。可以说是对于量价数据的”完全挖掘“，也不为过。

我并不擅长撰写教程，后续会慢慢更新我的心得。在这个项目临近结束时，我读到了《Advances in Financial Machine Learning》，其中很多内容与我的做法不谋而合，比如数据初筛，三重壁垒法。这可能说明了这些方法的普适性与有效性，如果您是一个算法交易爱好者，那么不妨读读这本书。


# Strcuture
Does such a simple project really need an introduction to the file structure?
- [Bot](#Bot) - Relevant code and information about trading strategies and the bot are still being written...（交易策略和bot的相关代码，相关介绍还在撰写中……）
  - models - 模型
  - strategies - 策略相关代码
    - reverse_detector.py - 调用ml，判断反转点
    - strategies.py - 策略本身的代码
    - strategy_utils.py
  - utils
    - data_utils.py
    - information.py  - 管理策略运行时需要的全部数据。暂存数据。
    - trade_utils.py  - Utility functions for placing orders.(下单相关的工具函数)
  - run_trade.py - Main program to run the overall trading bot, calling various trading strategy classes. (运行整体交易bot，调用各类交易策略的主程序)

- [Research](#Research) - In the research section, I document my exploration process regarding cryptocurrency-related trading signals/strategies, primarily divided into two categories: (在research部分记录了我对于加密货币相关交易信号/策略的每次探索过程，主要分为两类：)
  1. signals(信号)
      - [Moving Average and Trend of Prices.](./Research/trend_strategy.ipynb)
      - [Volatility and signal theta](./Research/mean_reversion.ipynb)
  3. Strategies(策略)
      - [Refining Signals Using Machine Learning](./Research/machine_learning)


## Next steps
近期会尽量完善注释，更新相关research代码。（We will strive to improve comments and update the relevant research code in the near future.）

### Join the community
- ⭐️ Star [`HengTrader` on GitHub](https://github.com/miaografa/HengTrader)
- 💖 Welcome anyone to contact me and join us.

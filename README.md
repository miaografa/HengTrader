# HengTrader ![image](https://img.shields.io/badge/HengTrader-0.000001%2B-blue)
> A project for algorithmic trading of cryptocurrencies.

From now on, you can automate the process of lossing money. 😼
现在起，你可以将输钱过程自动化了！

## Introduction 
The purpose of this project is to maximize the separation and independence of the "trading strategy," "backtesting," "order placement," and "data" components. This allows us to focus on the strategy itself when designing and backtesting trading strategies, simplifying the interactions between the strategy and other parts.

Additionally, I plan to directly develop the trading component based on the ccxt API. This way, even enthusiasts with minimal experience can easily run their own trading bot (and potentially lose money automatically🐽) without the need for significant additional effort.


# Strcuture
Does such a simple project really need an introduction to the file structure?
- [Bot](#Bot) - Relevant code and information about trading strategies and the bot are still being written...（交易策略和bot的相关代码，相关介绍还在撰写中……）
  - backtest.py
  - data_utils.py
  - run_trade.py - Main program to run the overall trading bot, calling various trading strategy classes. (运行整体交易bot，调用各类交易策略的主程序)
  - strategies.py - Records independent strategy objects.(记录独立的策略对象)
  - strategy_utils.py
  - trade_utils.py  - Utility functions for placing orders.(下单相关的工具函数)
- [Research](#Research) - In the research section, I document my exploration process regarding cryptocurrency-related trading signals/strategies, primarily divided into two categories: (在research部分记录了我对于加密货币相关交易信号/策略的每次探索过程，主要分为两类：)
  1. signals(信号)
      - [Moving Average and Trend of Prices.](./Research/trend_strategy.ipynb)
      - [Volatility and signal theta](./Research/mean_reversion.ipynb)
  3. Strategies(策略)
      - [Refining Signals Using Machine Learning](./Research/machine_learning)


# Bot

# Research

## Signals

## Strategies


## Next steps
This project has just begun completely... The recent main task is to complete the code for the backtesting framework. Then, there's also the need to adjust the file structure and improve comments and such. QAQ.
这个项目还完全刚刚开始……最近的主要工作是完成回测框架的代码。然后还要调整文件结构，完善注释之类的。QAQ

### Join the community
- ⭐️ Star [`HengTrader` on GitHub](https://github.com/miaografa/HengTrader)
- 💖 Welcome anyone to contact me and join us.

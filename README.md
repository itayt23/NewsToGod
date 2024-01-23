# NewsToGod

## Overview

The NewsToGod repository focuses on reading financial news sentiments and implementing a scoring system for ranking instruments. The sentiment analysis is performed using the Hugging Face FinBERT model. The user interface is built using SimpleGUI for ease of use.

## Functionality

### Main Window

The main window provides various functionalities through a clean and intuitive user interface:

- **Get Market Sentiment:**
  - Retrieve sentiment analysis for financial news related to markets.
  
- **Get Sectors Sentiment:**
  - Retrieve sentiment analysis for financial news related to sectors.

- **Load Markets Recommendation:**
  - Load previously saved recommendation data for markets.

- **Load Sectors Sentiment:**
  - Load previously saved sentiment data for sectors.

- **Connect TradeStation:**
  - Establish a connection to TradeStation for trading-related activities.

   ![Main Window](/images/main_window.png)


### TradeStation Window

The TradeStation window provides additional functionalities for trading activities:

- **Run Full Automate Strategy:**
  - Execute a fully automated trading strategy.

- **Run Semi Automate Strategy:**
  - Execute a semi-automated trading strategy.

- **Update Account:**
  - Fetch and update account data from TradeStation.

- **Show Portfolio:**
  - Display the current portfolio status.

- **Show Orders:**
  - Display the current list of orders.

- **Sectors and Markets Sentiment:**
  - View sentiment analysis results for sectors and markets.

- **Account Details:**
  - Display account-related information, including ID, cash balance, and equity.

- **Orders Column:**
  - View today's return, realized return (%), and unrealized return (%).

## Usage

To use the NewsToGod application, follow these steps:

1. **Connect to TradeStation:**
   - Click on "Connect TradeStation" to establish a connection.

2. **Get Sentiments:**
   - Use the "Get Market Sentiment" and "Get Sectors Sentiment" buttons to analyze financial news sentiments.

3. **Run Trading Strategies:**
   - Choose between "Run Full Automate Strategy" or "Run Semi Automate Strategy" to execute trading strategies.

4. **Update Account and View Portfolio:**
   - Periodically click on "Update Account" to fetch the latest account data.
   - Click on "Show Portfolio" to view the current portfolio status.

5. **Show Orders:**
   - Click on "Show Orders" to display the current list of orders.

## Notes

- The code uses Hugging Face FinBERT for sentiment analysis.
- Ensure that the required dependencies are installed (provide them in the `requirements.txt` file).

## Setup Instructions

1. Clone the repository.
2. Install dependencies using `pip install -r requirements.txt` (if applicable).
3. Run the main code using a Python interpreter.

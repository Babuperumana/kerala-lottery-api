# Kerala Lottery API 🎰

A fully automated, zero-maintenance API providing live and historical results for Kerala State Lotteries. This project automatically updates daily, maintaining a clean 7-day rolling window of the latest lottery results.

## Overview

This repository hosts a JSON API that provides detailed prize breakdowns, including the 1st prize down to the lowest consolation prizes. It is designed to be easily consumed by mobile applications, websites, and data analysts.

The data is fully automated via GitHub Actions, meaning `result.json` is always kept up-to-date with the latest live draws every day between 3:00 PM and 4:30 PM (IST).

## Endpoints

### Get Latest Results (7 Days)
- **URL**: `https://raw.githubusercontent.com/Babuperumana/kerala-lottery-api/main/result.json`
- **Method**: `GET`
- **Response Format**: `JSON`

### Data Structure

The API returns an array of objects representing the lottery draws from the last 7 days. Each object contains the date, the name of the lottery, and a detailed breakdown of all prizes.

```json
[
  {
    "date": "August 25 2026",
    "name": "STHREE-SAKTHI",
    "prizes": {
      "1st Prize": {
        "amount": "₹10000000 (1 Crore)",
        "numbers": [
          "SE 974999 (ERNAKULAM)"
        ]
      },
      "2nd Prize": {
        "amount": "₹500000 (5 Lakh)",
        "numbers": [
          "SB 123456"
        ]
      }
    }
  }
]
```

## Features
- **Live Updates**: The API updates incrementally while the draw is actively taking place.
- **Formatted Amounts**: Prize amounts are automatically converted and formatted into human-readable Indian Numbering systems (Lakhs and Crores).
- **Rolling Window**: Keeps your app lightweight by storing only the most recent 7 days of official results.
- **100% Uptime & Free**: Hosted statically on GitHub, meaning there are no servers to manage, no rate limits to worry about, and perfect uptime.

## Disclaimer

This API is provided for educational and informational purposes only. We do not guarantee the accuracy of the data, and users should always verify winning numbers with official publications.

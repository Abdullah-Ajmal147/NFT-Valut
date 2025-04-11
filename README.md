# NFTVault - MLM-Based NFT Trading Platform

NFTVault is a Django-based NFT trading platform that incorporates MLM (Multi-Level Marketing) mechanics, allowing users to trade NFTs and earn commissions through referrals.

## Features

- NFT Marketplace
- MLM Referral System
- NFT Staking
- User Authentication
- Commission Tracking
- Basic Analytics

## Tech Stack

- Django 5.0.2
- Django REST Framework
- Web3.py for blockchain integration
- Bootstrap 5 for frontend
- SQLite (for development)

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with:
```
SECRET_KEY=your-secret-key
DEBUG=True
WEB3_PROVIDER_URI=your-web3-provider-uri
```

4. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

## MLM Commission Structure

- Direct Referral: 10% commission
- Second Level: 5% commission

## License

MIT License 
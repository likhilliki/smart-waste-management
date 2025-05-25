BuildVerse - Smart Waste Management System
A modern waste management solution that combines AI-powered waste classification, blockchain tracking, and recycling rewards to promote sustainable waste disposal practices.

Features
AI-powered waste classification using YOLOv5
QR code generation for waste tracking
Blockchain-based transaction logging
Recycling credit reward system
Multi-user roles (Users, Recyclers, Admins)
Secure wallet integration
Tech Stack
Backend: Python Flask
Database: SQLAlchemy with SQLite/PostgreSQL
AI Model: YOLOv5 for waste classification
Frontend: HTML, CSS, JavaScript
Authentication: Flask-Login
Styling: Bootstrap 5
Getting Started
The application will automatically start when you click the Run button
Access the web interface at https://your-repl-url
Register as a user or recycler to begin using the platform
User Roles
Regular Users
Scan waste items using AI classification
Generate QR codes for waste tracking
Earn recycling credits
View transaction history
Manage digital wallet
Recyclers
Scan user-generated QR codes
Verify waste collection
Process recyclable materials
Track collection metrics
Administrators
Monitor system performance
Track user and recycler activity
View transaction history
Generate reports and analytics
Environment Variables
DATABASE_URL: Database connection string (defaults to SQLite)
SESSION_SECRET: Secret key for session management
Additional configuration can be set in app.py
Project Structure
├── app.py              # Main application configuration
├── routes.py           # Application routes
├── models.py           # Database models
├── blockchain.py       # Blockchain integration
├── waste_classifier.py # AI classification logic
├── templates/          # HTML templates
├── static/            
│   ├── css/           # Stylesheets
│   └── js/            # JavaScript files
Features in Detail
Waste Classification

AI-powered image recognition
Multiple waste category support
Real-time classification
Blockchain Tracking

Transparent waste journey
Immutable transaction records
Verifiable collection proof
Credit System

Reward for proper disposal
Credit accumulation
Redemption options
Security
Secure user authentication
Encrypted data storage
Protected API endpoints
Session management
Contributing
Feel free to fork this project and submit pull requests for any improvements.

License
This project is licensed under the MIT License.

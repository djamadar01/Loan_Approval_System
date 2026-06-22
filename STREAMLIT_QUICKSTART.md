# Streamlit Loan Application - Quick Start

## 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements_streamlit.txt

# 2. Make sure FastAPI backend is running
python server.py  # or python -m api.loan_application_api

# 3. In a new terminal, run Streamlit
streamlit run app.py

# 4. Open browser to: http://localhost:8501
```

## What You Get

### 🏠 **Home Page**
- System overview with key metrics
- Feature highlights
- Quick start button to begin application

### 📋 **Apply Page**
- 4-step loan application form
- Real-time validation with helpful hints
- Progress indicator
- Instant submission to backend

### 📊 **Status Page**
- Beautiful decision result display
- Risk gauges and confidence metrics
- Factor analysis with visualizations
- Conditions and required documents

### 📈 **Analytics Page**
- Application statistics
- Decision distribution pie chart
- Loan amount trends
- Application timeline
- Recent applications table

## Form Navigation

The 4-step form guides you through:

1. **Personal Info** → Name, email, age, location
2. **Employment** → Status, years, education, income
3. **Financial** → Credit score, savings, expenses, liabilities
4. **Loan Details** → Purpose, amount, tenure

Use Back/Next buttons to navigate. All data is saved as you go.

## Key Features

### ✨ Beautiful UI
- Color-coded decisions
- Interactive charts and gauges
- Responsive layout
- Professional branding

### 🔐 Smart Validation
- Real-time error checking
- Helpful hints for each field
- Clear error messages
- Prevents invalid submissions

### ⚡ Fast Processing
- Instant form validation
- Real-time backend communication
- Results in seconds
- Smooth navigation

### 📊 Rich Analytics
- Decision statistics
- Application trends
- Risk assessment
- Historical tracking

## Sidebar Controls

The left sidebar provides:
- Navigation between pages
- System status (online/offline indicator)
- Recent applications quick view
- Brand information

## Typical Workflow

1. **Home** → Click "Start Your Application"
2. **Apply Step 1** → Fill personal info, click Next
3. **Apply Step 2** → Enter employment data, click Next
4. **Apply Step 3** → Provide financial info, click Next
5. **Apply Step 4** → Specify loan details, click Submit
6. **Status** → Review decision results
7. **Analytics** → See trends and statistics

## Customization

### Change API Endpoint
Edit the top of `app.py`:
```python
API_BASE_URL = "http://your-server.com:8000"
```

### Add New Loan Purpose
Add to `LOAN_PURPOSES` list:
```python
LOAN_PURPOSES = [
    "home_purchase",
    "your_new_purpose",
    ...
]
```

### Adjust Color Scheme
Modify color dictionaries:
```python
DECISION_COLORS = {
    "approved": "#10B981",  # Change hex code
    ...
}
```

## Troubleshooting

### Backend Not Found
```bash
# Check if FastAPI is running on port 8000
curl http://localhost:8000/health

# If not, start it:
python server.py
```

### Form Won't Submit
- Check all fields are filled (red error messages show issues)
- Verify backend is online (check sidebar indicator)
- Review browser console for errors

### Slow Performance
- Clear browser cache
- Restart Streamlit: Press `C` then restart
- Check backend is responding quickly

## Files Structure

```
demo/
├── app.py                    # Main Streamlit application
├── requirements_streamlit.txt # Python dependencies
├── server.py                # FastAPI backend
├── STREAMLIT_QUICKSTART.md  # This file
├── STREAMLIT_APP_GUIDE.md   # Detailed documentation
└── ...other backend files
```

## Environment Variables (Optional)

```bash
# Set API endpoint via environment
export API_BASE_URL="http://your-api-server.com:8000"

# Run with custom port
streamlit run app.py --server.port 8502

# Enable debug logging
streamlit run app.py --logger.level=debug
```

## Next Steps

1. **Try the demo:**
   - Fill out a test application
   - Review decision results
   - Check analytics page

2. **Customize:**
   - Change colors to match brand
   - Add/remove loan purposes
   - Adjust validation rules

3. **Deploy:**
   - Use Docker for containerization
   - Deploy to cloud (AWS, GCP, Azure)
   - Set up HTTPS in production

4. **Enhance:**
   - Add user authentication
   - Integrate with database
   - Add document upload
   - Enable notifications

## Support

For detailed documentation, see: `STREAMLIT_APP_GUIDE.md`

For API documentation, see: `API_DOCUMENTATION.md`

---

**Ready to go? Start with:**
```bash
streamlit run app.py
```

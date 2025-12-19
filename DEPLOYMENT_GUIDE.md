# Deployment Guide for Golf Swing Analyzer

## 🚀 Deploy to Render (Free Tier)

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for deployment"

# Create a new repository on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/golf-swing-analyzer.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

1. **Go to** [render.com](https://render.com) and sign up/login

2. **Click "New +"** → **"Web Service"**

3. **Connect GitHub repository**
   - Click "Connect account" if first time
   - Select your `golf-swing-analyzer` repository

4. **Configure the service:**
   - **Name**: `golf-swing-analyzer` (or whatever you prefer)
   - **Environment**: `Python 3`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**:
     ```
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```
     gunicorn app:app
     ```

5. **Advanced Settings** (click to expand):
   - Add environment variable:
     - **Key**: `PYTHON_VERSION`
     - **Value**: `3.11.0`

   - **Auto-Deploy**: `Yes` (recommended)

6. **Click "Create Web Service"**

7. **Wait for deployment** (5-10 minutes)
   - Watch the logs for any errors
   - Render will install FFmpeg and all dependencies automatically

8. **Get your URL**
   - Once deployed, you'll get a URL like: `https://golf-swing-analyzer.onrender.com`
   - Share this with your friends!

---

## ⚙️ Important Notes

### Free Tier Limitations:
- **Sleeps after 15 min of inactivity** - First request after sleep takes ~30 seconds
- **750 hours/month** - Should be enough for personal use
- **Limited CPU/RAM** - Processing might be slower than local

### Upgrading to Paid ($7/month):
- No sleep
- Better performance
- More RAM for faster video processing
- Click "Upgrade" in Render dashboard

---

## 🐛 Troubleshooting

### Build fails with "FFmpeg not found"
- Check that `aptfile` exists in your repo
- Render should automatically install packages from `aptfile`

### App crashes on video processing
- Free tier might run out of memory for very large videos
- Try smaller videos (< 50MB) or upgrade to paid tier

### "Application Error" when visiting site
- Check Render logs for errors
- Common issue: Missing environment variables
- Make sure Python version is set correctly

### Videos don't play in browser
- Check that FFmpeg installed correctly in logs
- Look for "Converting to browser-compatible format..." message

---

## 📊 Monitoring

**View logs:**
1. Go to Render dashboard
2. Click on your service
3. Click "Logs" tab
4. Watch for errors in real-time

**Check disk usage:**
- Uploaded videos are automatically deleted after 2 hours
- Check "Metrics" tab in Render for disk usage

---

## 🔒 Security Recommendations

### For production use:
1. **Add rate limiting** to prevent abuse
2. **Add user authentication** if you want private access
3. **Set up custom domain** (optional)
4. **Enable HTTPS** (Render does this automatically)

### Optional: Add basic password protection

Add to `app.py` before routes:
```python
from functools import wraps
from flask import request, Response

def check_auth(username, password):
    return username == 'golf' and password == 'YOUR_PASSWORD_HERE'

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response('Login required', 401,
                          {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return decorated

# Add @requires_auth decorator to routes:
@app.route('/')
@requires_auth
def index():
    return render_template('index.html')
```

---

## 🎉 Success!

Your app is now live! Share the URL with your friends.

**Next steps:**
- Test with different videos
- Monitor usage in Render dashboard
- Consider upgrading if you get lots of traffic
- Check AUTO_SYNC_NOTES.md for future improvements

---

## 💰 Cost Breakdown

| Tier | Price | Best For |
|------|-------|----------|
| Free | $0 | Testing, personal use |
| Starter | $7/mo | Small group of friends |
| Standard | $25/mo | Production, lots of users |

---

Need help? Check Render docs or open an issue on GitHub!

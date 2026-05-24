# Production Deployment Guide

This guide details step-by-step pathways to deploy the **Job Market Analytics Dashboard Platform** to cloud infrastructure. 

Since the application uses a **Pure-Python Data Architecture** (completely bypassing complex C-extensions, Pandas, NumPy, or Streamlit compilation limitations), it is extremely lightweight, consumes less than **40 MB of RAM**, and can run on any micro-instance, serverless container, or free hosting tier!

---

## Option 1: Containerized Deployment (Docker - Recommended)

Docker is the industry standard for production-ready setups. We have provided a [`Dockerfile`](../Dockerfile) in the root of the workspace.

### 1. Build and Test Locally
To verify the Docker container locally:
```bash
# Build the docker image
docker build -t job-market-dashboard .

# Run the container exposing port 8501
docker run -p 8501:8501 job-market-dashboard
```
Open **`http://localhost:8501`** in your browser to confirm system health.

### 2. Deploy to Serverless Container Platforms (GCP Cloud Run / AWS App Runner)
Serverless containers are highly scalable and cheap because they automatically scale to zero when there is no traffic.

#### Google Cloud Run (GCP)
1. Install the Google Cloud SDK.
2. Build and submit your container directly to Google Container Registry (GCR):
   ```bash
   gcloud builds submit --tag gcr.io/your-project-id/job-market-dashboard
   ```
3. Deploy the container to Cloud Run:
   ```bash
   gcloud run deploy job-market-dashboard \
     --image gcr.io/your-project-id/job-market-dashboard \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 8501
   ```
4. GCP will provide a secure HTTPS URL (e.g., `https://job-market-dashboard-xyz.run.app`).

#### AWS App Runner
1. Push your docker image to **Amazon ECR** (Elastic Container Registry).
2. Go to the AWS App Runner Console, click **Create Service**.
3. Choose **Container Registry** and select your ECR image repository.
4. Set the port to `8501` in the configuration.
5. Launch! AWS manages auto-scaling and HTTPS certificates natively.

---

## Option 2: Platform-as-a-Service (Render / Railway / Heroku)

These platforms require zero command-line infrastructure experience and integrate directly with your GitHub repository.

### Render Deployment (Render.com - Highly Recommended Free Tier)
1. Push your project code to a **GitHub Repository**.
2. Log in to [Render](https://render.com) and click **New** -> **Web Service**.
3. Connect your GitHub repository.
4. Configure the settings:
   - **Name**: `job-market-analytics`
   - **Environment**: `Python 3` (or choose `Docker` since the repo has a `Dockerfile`!)
   - **Build Command**: `pip install -r requirements.txt` (only needed if using Python environment directly)
   - **Start Command**: `python app/server.py`
   - **Instance Type**: **Free Tier** (Since we consume minimal resources, the free tier is perfect!)
5. Render will automatically build the repository and deploy it on a secure `https://job-market-analytics.onrender.com` domain.

---

## Option 3: Virtual Private Server (VPS - DigitalOcean / AWS EC2 / Linode)

If you are deploying to a standard Linux Ubuntu instance, configure it to run permanently using a `systemd` daemon and Nginx.

### 1. Clone & Set Up Virtual Environment
On your Linux VPS:
```bash
cd /var/www
git clone <your-repo-url> data-analytics
cd data-analytics

# Create and activate python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run orchestrator to compile database & ML models
python run.py
```

### 2. Configure Systemd Service (Autostart on boot)
To make the dashboard run permanently as a background system daemon:
1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/job-market.service
   ```
2. Paste the following configuration:
   ```ini
   [Unit]
   Description=Job Market Analytics Daemon
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/var/www/data-analytics
   ExecStart=/var/www/data-analytics/.venv/bin/python app/server.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable job-market
   sudo systemctl start job-market
   ```
4. Verify server running status:
   ```bash
   sudo systemctl status job-market
   ```

### 3. Nginx Reverse Proxy (Exposing to SSL Domain)
Configure Nginx to route incoming standard HTTP/HTTPS traffic (port 80/443) directly to our local port `8501`:
1. Edit your Nginx configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/default
   ```
2. Replace or update the `location /` block:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:8501;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```
3. Test and restart Nginx:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```
4. Enable Let's Encrypt SSL for secure `https://`:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

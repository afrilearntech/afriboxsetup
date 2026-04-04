sudo cp deployment/websocket/afriboxdaphne.service /etc/systemd/system/afriboxdaphne.service
sudo systemctl daemon-reload
sudo systemctl enable afriboxdaphne
sudo systemctl start afriboxdaphne

sudo cp deployment/websocket/nginx.conf /etc/nginx/sites-available/afribox
sudo ln -s /etc/nginx/sites-available/afribox /etc/nginx/sites-enabled/afribox
sudo nginx -t
sudo systemctl restart nginx
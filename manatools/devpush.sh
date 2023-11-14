git add .
if [ -z "$1" ]; then echo "oops";
else
    git commit -m "$1"
    git push
    ssh -i ~/.ssh/fresh_cut_shirts.pem -t root@143.198.79.233 "cd /home/ubuntu/manatools.com/ ; git pull ; source /r.sh"
fi

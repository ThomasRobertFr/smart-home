rsync -ravh \
  --include="data/config*" \
  --exclude="data/*" \
  --exclude='.*' \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  ./ \
  pi@192.168.1.10:dev/smart-home/

#! /bin/bash

echo reporting to: $1, $2
curl "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=$1" \
  -H "Content-Type: application/json" \
  -d "
  {
      \"msgtype\": \"text\",
      \"text\":{
          \"content\": \"$2\"
      }
  }"

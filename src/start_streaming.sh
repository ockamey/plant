#!/bin/bash
STREAMING_URL=<streaming URL>
raspivid -t 0 -w 1280 -h 720 -fps 25 -g 75 -fl -o - | ffmpeg -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 -i pipe:0 -c:v copy -c:a aac -strict experimental -f flv -f flv $STREAMING_URL
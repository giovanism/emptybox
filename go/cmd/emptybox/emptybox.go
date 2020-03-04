package main

import (
	"flag"

	emptybox "github.com/giovanism/emptybox/go/internal/emptybox"
)

const defaultListenAddress = "127.0.0.1:8000"

func main() {
	bindAddress := flag.String("bind", defaultListenAddress, "Address to listen")
	init := flag.Bool("init", false, "Initialize S3 Bucket")

	flag.Parse()

	if *init {
		emptybox.InitBucket()
	} else {
		emptybox.ServeHTTP(*bindAddress)
	}
}

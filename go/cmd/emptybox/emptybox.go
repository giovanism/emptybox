package main

import (
	"flag"

	emptybox "github.com/giovanism/emptybox/go/internal/emptybox"
)

func main() {
	init := flag.Bool("init", false, "Initialize S3 Bucket")

	flag.Parse()

	if *init {
		emptybox.InitBucket()
	} else {
		emptybox.ServeHTTP()
	}
}

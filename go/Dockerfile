FROM golang:alpine

ADD . /go/src/github.com/giovanism/emptybox/go

WORKDIR /go/src/github.com/giovanism/emptybox/go
RUN go build github.com/giovanism/emptybox/go/cmd/emptybox

FROM alpine

COPY --from=0 /go/src/github.com/giovanism/emptybox/go/emptybox /go/bin/emptybox

CMD ["/go/bin/emptybox"]

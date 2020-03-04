package emptybox

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"mime"
	"net/http"
	"os"
	"path/filepath"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/google/uuid"
)

const (
	defaultListenAddress = "127.0.0.1:8000"
)

var (
	mainSiteAddress = getEnvOrDefault("EMPTYBOX_SITE", "http://localhost:3000")
	s3Host          = os.Getenv("EMPTYBOX_S3_HOST")
	s3Bucket        = os.Getenv("EMPTYBOX_S3_BUCKET")
	s3AccessKey     = os.Getenv("EMPTYBOX_S3_ACCESS_KEY")
	s3SecretKey     = os.Getenv("EMPTYBOX_S3_SECRET_KEY")
	s3client        = *newS3Client()

	errKey = errors.New("KeyError")
)

func index(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, mainSiteAddress, http.StatusPermanentRedirect)
}

func upload(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodPost {
		jsonEnc := json.NewEncoder(w)

		uploadType := r.FormValue("type")
		var uploadFile io.ReadCloser
		var fileName string

		defer func() {
			if r := recover(); r != nil {
				if err, ok := r.(error); ok && err == errKey {
					log.Printf("%v", err)
					errData := map[string]string{"msg": "Invalid Request"}

					w.WriteHeader(http.StatusBadRequest)
					jsonEnc.Encode(errData)
				}
			}
		}()

		if uploadType == "file" {
			mulFile, mulFileHeader, err := r.FormFile("file")
			if err != nil {
				panic(errKey)
			}

			uploadFile = mulFile
			fileName = mulFileHeader.Filename

		} else if uploadType == "url" {
			url := r.FormValue("url")
			response, err := http.Get(url)
			if err != nil {
				panic(errKey)
			}
			contentDisposition := response.Header.Get("Content-Disposition")
			_, params, err := mime.ParseMediaType(contentDisposition)
			if err != nil {
				panic(err)
			}

			uploadFile = response.Body
			fileName, _ = params["filename"]

		} else {
			panic(errKey)
		}

		content, err := ioutil.ReadAll(uploadFile)
		if err != nil {
			panic(err)
		}

		body := bytes.NewReader(content)
		key := genKey(fileName)
		input := s3.PutObjectInput{Bucket: &s3Bucket, Key: &key, Body: body}
		s3client.PutObject(&input)

		saveData := map[string]string{
			"msg":      "Saved",
			"filename": key,
		}

		jsonEnc.Encode(saveData)

	} else {
		w.WriteHeader(http.StatusMethodNotAllowed)
	}
}

func stats(w http.ResponseWriter, r *http.Request) {
	input := s3.ListObjectsV2Input{Bucket: &s3Bucket}
	ls, err := s3client.ListObjectsV2(&input)
	if err != nil {
		fmt.Println(err.Error())
		panic(err)
	}

	statsData := map[string]*int64{"fileCount": ls.KeyCount}

	jsonEnc := json.NewEncoder(w)
	jsonEnc.Encode(statsData)
}

func ServeHTTP(bindAddress string) {
	server := http.NewServeMux()
	server.HandleFunc("/", index)
	server.HandleFunc("/upload/", upload)
	server.HandleFunc("/stats/", stats)

	log.Print("========================= emptybox =========================")
	log.Printf("Server starting at %s\n", bindAddress)
	http.ListenAndServe(bindAddress, server)
}

// genKey generate UUID4 based S3 key. The generated key also account for file
// extension for convenience.
func genKey(key string) string {
	u, err := uuid.NewRandom()

	if err != nil {
		fmt.Println(err.Error())
		panic(err)
	}

	if key != "" {
		base := filepath.Base(key)
		ext := filepath.Ext(key)

		if ext != "" {
			return u.String() + ext
		}

		if base[0] == '.' {
			return u.String() + base
		}
	}

	return u.String()
}

func getEnvOrDefault(key, fallback string) string {
	if value, ok := os.LookupEnv(key); ok {
		return value
	}

	return fallback
}

func setAWSCredentialsEnv() {
	os.Setenv("AWS_ACCESS_KEY_ID", s3AccessKey)
	os.Setenv("AWS_SECRET_ACCESS_KEY", s3SecretKey)
}

func newS3Client() *s3.S3 {
	// Configure to use MinIO Server
	s3Config := &aws.Config{
		Credentials:      credentials.NewStaticCredentials(s3AccessKey, s3SecretKey, ""),
		Endpoint:         aws.String(s3Host),
		Region:           aws.String("us-east-1"),
		DisableSSL:       aws.Bool(true),
		S3ForcePathStyle: aws.Bool(true),
	}

	newSession := session.New(s3Config)
	return s3.New(newSession)
}

func InitBucket() {
	_, err := s3client.CreateBucket(&s3.CreateBucketInput{
		Bucket: &s3Bucket,
	})

	if err != nil {
		fmt.Println(err.Error())
		panic(err)
	}

	readOnlyAnonUserPolicy := map[string]interface{}{
		"Version": "2012-10-17",
		"Statement": []map[string]interface{}{
			{
				"Sid":       "AddPerm",
				"Effect":    "Allow",
				"Principal": "*",
				"Action": []string{
					"s3:GetObject",
				},
				"Resource": []string{
					fmt.Sprintf("arn:aws:s3:::%s/*", s3Bucket),
				},
			},
		},
	}

	policy, err := json.Marshal(readOnlyAnonUserPolicy)
	if err != nil {
		panic(err)
	}

	_, err = s3client.PutBucketPolicy(&s3.PutBucketPolicyInput{
		Bucket: &s3Bucket,
		Policy: aws.String(string(policy)),
	})

	if err != nil {
		fmt.Println(err.Error())
		panic(err)
	}
}

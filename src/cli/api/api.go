package api

import (
	"net/http"
)

type Client struct {
	BaseURL    string
	HTTPClient *http.Client
}

func NewClient(url string) *Client {
	return &Client{
		BaseURL:    url,
		HTTPClient: &http.Client{},
	}
}

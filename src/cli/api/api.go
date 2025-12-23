package api

import (
	"bytes"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
)

func NewClient(url string) *Client {
	return &Client{
		BaseURL:    url,
		HTTPClient: &http.Client{},
	}
}

// following methods have been generated
// based on the admin-api service implementation
//
// Gemini 3 Pro
// No previous context
// Prompt:
//
// Based on the following FastAPI implementation,
// implement the following methods in this Golang skeleton
//
// api.go:
// <client + function signatures without arguments>
//
// api.py:
// <route implementations from admin-api service>

func (client *Client) UploadBatch(files []string, manifestPath string, manifestStr string) (*UploadBatchResponse, error) {
	var buf bytes.Buffer
	writer := multipart.NewWriter(&buf)

	for _, file := range files {
		f, err := os.Open(file)
		if err != nil {
			return nil, err
		}

		defer f.Close()

		part, err := writer.CreateFormFile("files", filepath.Base(file))
		if err != nil {
			return nil, err
		}
		_, err = io.Copy(part, f)
		if err != nil {
			return nil, err
		}
	}

	if manifestPath != "" {
		f, err := os.Open(manifestPath)
		if err != nil {
			return nil, err
		}
		defer f.Close()
		part, err := writer.CreateFormFile("manifest_file", filepath.Base(manifestPath))
		if err != nil {
			return nil, err
		}
		_, err = io.Copy(part, f)
		if err != nil {
			return nil, err
		}
	} else if manifestStr != "" {
		_ = writer.WriteField("manifest_str", manifestStr)
	}

	writer.Close()

	req, err := http.NewRequest("POST", client.BaseURL+"/fer/data/upload", &buf)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())

	resp, err := client.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var uploadResp UploadBatchResponse
	if err := json.NewDecoder(resp.Body).Decode(&uploadResp); err != nil {
		return nil, err
	}

	return &uploadResp, nil
}

func (client *Client) StartTraining() (*StartTrainingResponse, error) {
	req, err := http.NewRequest("POST", client.BaseURL+"/fer/model/train", nil)
	if err != nil {
		return nil, err
	}

	resp, err := client.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var trainingResp StartTrainingResponse
	if err := json.NewDecoder(resp.Body).Decode(&trainingResp); err != nil {
		return nil, err
	}

	return &trainingResp, nil
}

func (client *Client) SelectModel(version string) (*SelectModelResponse, error) {
	payload := map[string]string{"model_version": version}
	body, _ := json.Marshal(payload)

	req, err := http.NewRequest("POST", client.BaseURL+"/fer/model/select", bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.HTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var selectResp SelectModelResponse
	if err := json.NewDecoder(resp.Body).Decode(&selectResp); err != nil {
		return nil, err
	}

	return &selectResp, nil
}

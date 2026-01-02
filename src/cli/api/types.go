// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

package api

import (
	"encoding/json"

	batchv1 "k8s.io/api/batch/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"net/http"
)

type Client struct {
	BaseURL    string
	HTTPClient *http.Client
}

type FailedFileDetail struct {
	Filename string `json:"filename"`
	Reason   string `json:"reason"`
}

type UploadBatchResponse struct {
	Status     string `json:"status"`
	BatchID    string `json:"batch_id"`
	SavedFiles struct {
		Count int `json:"count"`
	} `json:"saved_files"`
	FailedFiles struct {
		Count  int                `json:"count"`
		Detail []FailedFileDetail `json:"detail"`
	} `json:"failed_files"`
}

type StartTrainingResponse struct {
	JobStatus       *batchv1.JobStatus `json:"job_status"`
	Metadata        metav1.ObjectMeta  `json:"metadata"`
	ModelVersion    string             `json:"model_version"`
	TrainingSetSize int                `json:"training_set_size"`
}

type SelectModelResponse struct {
	Status   json.RawMessage `json:"status"`
	Message  string          `json:"message,omitempty"`
	Path     string          `json:"path,omitempty"`
	NewModel *struct {
		Version string `json:"version"`
		Path    string `json:"path"`
	} `json:"new_model,omitempty"`
}

type ModelMetadata struct {
	ValAccuracy *float64 `json:"val_accuracy,omitempty"`
	Hyperparams struct {
		LearningRate float64 `json:"learning_rate"`
		Epochs       int     `json:"epochs"`
	} `json:"hyperparams"`
	Data struct {
		ValFraction float64 `json:"val_fraction"`
		BatchSize   int     `json:"batch_size"`
	} `json:"data"`
}

type ModelInfo struct {
	Version  string         `json:"version"`
	Metadata *ModelMetadata `json:"metadata,omitempty"`
}

type GetModelsResponse struct {
	Count    int         `json:"count"`
	Versions []string    `json:"versions"`
	Models   []ModelInfo `json:"models"`
}

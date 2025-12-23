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
	BatchID           string         `json:"batch_id"`
	Count             int            `json:"count"`
	LabelDistribution map[string]int `json:"label_distribution"`
}

type ModelInfo struct {
	Version  string         `json:"version"`
	Metadata *ModelMetadata `json:"metadata"` // nullable
}

type GetModelsResponse struct {
	Count    int         `json:"count"`
	Versions []string    `json:"versions"`
	Models   []ModelInfo `json:"models"`
}

package api

import (
	"blundr-cli/utils"
	"bufio"
	"encoding/json"
	"fmt"
	"strings"

	appsv1 "k8s.io/api/apps/v1"
)

func SelectModel(client *Client, reader *bufio.Reader) error {
	fmt.Print("\nEnter model version (e.g. v1): ")

	model, err := reader.ReadString('\n')
	if err != nil {
		return err
	}

	model = strings.TrimSpace(model)
	if model == "" {
		return fmt.Errorf("model version cannot be empty")
	}

	return SelectModelNonInteractive(client, model)
}

func SelectModelNonInteractive(client *Client, model string) error {
	response, err := utils.RunWithLoadingAnimation(
		"Selecting model",
		func() (*SelectModelResponse, error) {
			return client.SelectModel(model)
		},
	)
	if err != nil {
		return fmt.Errorf("%w", err)
	}

	fmt.Println("\n--- Model Selection Result ---")

	if response.NewModel == nil {
		return fmt.Errorf("unexpected response from API (missing new_model)")
	}

	fmt.Printf("Model version: %s\n", response.NewModel.Version)
	fmt.Printf("Model path:    %s\n", response.NewModel.Path)

	var deployStatus appsv1.DeploymentStatus
	if err := json.Unmarshal(response.Status, &deployStatus); err != nil {
		return fmt.Errorf("failed to parse deployment status: %w", err)
	}

	fmt.Println("\nDeployment status:")
	fmt.Printf("  Replicas:         %d\n", deployStatus.Replicas)
	fmt.Printf("  Ready replicas:   %d\n", deployStatus.ReadyReplicas)
	fmt.Printf("  Updated replicas: %d\n", deployStatus.UpdatedReplicas)
	fmt.Printf("  Available:        %d\n", deployStatus.AvailableReplicas)

	return nil
}

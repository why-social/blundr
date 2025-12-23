package api

import (
	"blundr-cli/utils"
	"fmt"
)

func TrainModel(client *Client) error {
	response, err := utils.RunWithLoadingAnimation("Submitting training job",
		func() (*StartTrainingResponse, error) {
			return client.StartTraining()
		})

	if err != nil {
		return fmt.Errorf("API request failed: %w", err)
	}

	fmt.Println("\n--- Training Job Submitted ---")
	fmt.Printf("Model Version:       %s\n", response.ModelVersion)
	fmt.Printf("Training Set Size:   %d samples\n", response.TrainingSetSize)

	if response.JobStatus != nil {
		fmt.Printf("Succeeded Pods:      %d\n", response.JobStatus.Succeeded)
		fmt.Printf("Failed Pods:         %d\n", response.JobStatus.Failed)
		fmt.Printf("Active Pods:         %d\n", response.JobStatus.Active)
	}

	fmt.Println("Job metadata:")
	fmt.Printf("  Name:        %s\n", response.Metadata.Name)
	fmt.Printf("  Namespace:   %s\n", response.Metadata.Namespace)
	fmt.Printf("  CreationTime:%s\n", response.Metadata.CreationTimestamp.String())

	return nil
}

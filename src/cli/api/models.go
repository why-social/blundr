// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

package api

import (
	"blundr-cli/utils"
	"fmt"
	"sort"
)

func PrintModels(client *Client) error {
	response, err := utils.RunWithLoadingAnimation(
		"Fetching models",
		func() (*GetModelsResponse, error) {
			return client.GetModels()
		},
	)

	if err != nil {
		return fmt.Errorf("API request failed: %w", err)
	}

	if response.Count == 0 {
		fmt.Println("No models found.")

		return nil
	}

	sort.Strings(response.Versions)

	fmt.Println("\n--- Available Models ---")
	fmt.Printf("Total models: %d\n\n", response.Count)

	for _, model := range response.Models {
		fmt.Printf("Version: %s\n", model.Version)

		if model.Metadata == nil {
			fmt.Println("  Metadata: unavailable")
		} else {
			if model.Metadata.ValAccuracy != nil {
				fmt.Printf("  Validation Accuracy: %.2f\n", *model.Metadata.ValAccuracy)
			}

			fmt.Println("  Hyperparameters:")
			fmt.Printf("    Learning Rate: %.4f\n", model.Metadata.Hyperparams.LearningRate)
			fmt.Printf("    Epochs: %d\n", model.Metadata.Hyperparams.Epochs)

			fmt.Println("  Data Info:")
			fmt.Printf("    Validation Fraction: %.2f\n", model.Metadata.Data.ValFraction)
			fmt.Printf("    Batch Size: %d\n", model.Metadata.Data.BatchSize)
		}

		fmt.Println()
	}

	return nil
}

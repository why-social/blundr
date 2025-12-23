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
			fmt.Printf("  Batch ID: %s\n", model.Metadata.BatchID)
			fmt.Printf("  Samples: %d\n", model.Metadata.Count)

			if len(model.Metadata.LabelDistribution) > 0 {
				fmt.Println("  Label distribution:")
				for label, count := range model.Metadata.LabelDistribution {
					fmt.Printf("    - %s: %d\n", label, count)
				}
			}
		}

		fmt.Println()
	}

	return nil
}

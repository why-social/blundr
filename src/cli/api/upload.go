// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

package api

import (
	"blundr-cli/utils"
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func UploadBatch(client *Client, reader *bufio.Reader) error {
	dirPath, err := pickImageDirectory(reader)

	if err != nil {
		return fmt.Errorf("failed to get directory path: %w", err)
	}

	if dirPath == "" {
		return fmt.Errorf("directory path cannot be empty")
	}

	manifestPath, err := pickManifest(reader)

	if err != nil {
		return fmt.Errorf("failed to get manifest path: %w", err)
	}

	if manifestPath == "" {
		return fmt.Errorf("manifest path cannot be empty")
	}

	return UploadBatchNonInteractive(client, dirPath, manifestPath)
}

func UploadBatchNonInteractive(client *Client, dirPath, manifestPath string) error {
	info, err := os.Stat(dirPath)
	if err != nil || !info.IsDir() {
		return fmt.Errorf("invalid directory path: %s", dirPath)
	}

	fmt.Println("Scanning directory for images...")
	var filesToUpload []string

	err = filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.ToLower(filepath.Ext(path)) == ".jpg" {
			filesToUpload = append(filesToUpload, path)
		}

		return nil
	})

	if err != nil {
		return fmt.Errorf("error scanning directory: %w", err)
	}

	if len(filesToUpload) == 0 {
		return fmt.Errorf("no valid image files found in %s", dirPath)
	}

	fmt.Printf("Found %d image files.\n", len(filesToUpload))

	if _, err := os.Stat(manifestPath); err != nil {
		return fmt.Errorf("manifest file does not exist: %s", manifestPath)
	}

	fmt.Println("")
	response, err := utils.RunWithLoadingAnimation("Uploading batch",
		func() (*UploadBatchResponse, error) {
			return client.UploadBatch(filesToUpload, manifestPath, "")
		})

	if err != nil {
		return fmt.Errorf("API request failed: %w", err)
	}

	fmt.Println("\n--- Upload Report ---")
	fmt.Printf("Status:   %s\n", strings.ToUpper(response.Status))
	fmt.Printf("Batch ID: %s\n", response.BatchID)
	fmt.Printf("Saved:    %d files\n", response.SavedFiles.Count)

	if response.FailedFiles.Count > 0 {
		fmt.Printf("Failed:   %d files\n", response.FailedFiles.Count)
		fmt.Println("\nFailure Details:")

		for index, detail := range response.FailedFiles.Detail {
			fmt.Printf("  %d. [%s]: %s\n", index+1, detail.Filename, detail.Reason)
		}
	} else {
		fmt.Println("All files uploaded successfully.")
	}

	return nil
}

func pickImageDirectory(reader *bufio.Reader) (string, error) {
	fmt.Print("\nEnter the path to the image directory: ")
	dirPath, err := reader.ReadString('\n')

	if err != nil {
		return "", err
	}

	return strings.TrimSpace(dirPath), nil
}

func pickManifest(reader *bufio.Reader) (string, error) {
	fmt.Print("\nEnter the path to manifest.csv file: ")
	filePath, err := reader.ReadString('\n')

	if err != nil {
		return "", err
	}

	return strings.TrimSpace(filePath), nil
}

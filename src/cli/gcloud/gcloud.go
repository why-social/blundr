package gcloud

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/exec"

	"blundr-cli/utils"

	"cloud.google.com/go/storage"
)

// returns true if gcloud is present
func checkInstallation() bool {
	_, err := exec.LookPath("gcloud")
	if err != nil {
		fmt.Print(`
Google Cloud SDK (gcloud) is not installed.

Please install it from:
https://cloud.google.com/sdk/docs/install
`)
		return false
	}

	return true
}

// returns true if user is logged in
func checkLogin() bool {
	cmd := exec.Command("gcloud", "auth", "application-default", "print-access-token")

	err := cmd.Run()
	if err == nil {
		return true
	}

	return false
}

// returns true if user successfully logged in
func attemptLogin() bool {
	fmt.Println("Opening browser for Google Cloud login...")

	loginCmd := exec.Command("gcloud", "auth", "application-default", "login")
	loginCmd.Stdin = os.Stdin
	loginCmd.Stdout = os.Stdout
	loginCmd.Stderr = os.Stderr

	if err := loginCmd.Run(); err != nil {
		fmt.Println("Failed to complete Google Cloud login.")

		return false
	}

	return true
}

// returns true if the user has access to a project
func checkProjectAccess(projectID string) bool {
	var stderr bytes.Buffer
	cmd := exec.Command("gcloud", "projects", "describe", projectID)
	cmd.Stderr = &stderr

	if err := cmd.Run(); err != nil {
		return false
	}

	return true
}

// returns true if credentials are usable
func checkCredentials(context context.Context) bool {
	_, err := storage.NewClient(context)

	if err != nil {
		fmt.Printf(`
Google Cloud credentials are present, but unusable.

Error:
%s
`, err)

		return false
	}

	return true
}

func EnsureGCloudAccess(context context.Context, projectId string) bool {
	if !checkInstallation() {
		return false
	}

	if !checkCredentials(context) || !checkLogin() {
		if !utils.PromptYesOrNo("Google Cloud login required. Do you want to log in now? (y/n): ") {
			fmt.Println("Login required to continue.")

			return false
		}

		if !attemptLogin() {
			return false
		}
	}

	if !checkProjectAccess(projectId) {
		fmt.Printf(`
You do not have access to the Google Cloud project "%s".
`, projectId)

		if utils.PromptYesOrNo("Do you want to switch or log in with another Google account? (y/n): ") {
			if !attemptLogin() {
				return false
			}

			if !checkProjectAccess(projectId) {
				fmt.Println("Selected account still does not have access.")

				return false
			}
		} else {
			return false
		}
	}

	if !checkCredentials(context) {
		return false
	}

	fmt.Println("Google Cloud authentication and project access verified.")

	return true
}

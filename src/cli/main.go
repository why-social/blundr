package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"

	"blundr-cli/api"
	"blundr-cli/gcloud"

	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load()
	adminAPIUrl := os.Getenv("ADMIN_API_URL")
	if adminAPIUrl == "" {
		adminAPIUrl = "http://localhost:42069"
	}

	context := context.Background()
	if !gcloud.EnsureGCloudAccess(context, "blundr") {
		return
	}

	loopOptions(api.NewClient(adminAPIUrl))
}

func loopOptions(client *api.Client) {
	reader := bufio.NewReader(os.Stdin)

	choice := ""
	for choice != "0" {
		fmt.Printf(`
Select an action (F.E.R. Service):

1) Get existing models
2) Upload training data
3) Train a new model
4) Update active model

0) Exit

Enter choice: `)

		input, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(input)

		switch choice {
		case "1":
			// TODO
		case "2":
			// TODO
		case "3":
			// TODO
		case "4":
			// TODO
		case "", "0":
			// ignored
		default:
			fmt.Println("Invalid option, try again.")
		}
	}
}

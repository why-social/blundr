package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"slices"
	"strings"

	"blundr-cli/api"
	"blundr-cli/gcloud"
	"blundr-cli/utils"

	"github.com/joho/godotenv"
)

func main() {
	_ = godotenv.Load()
	adminAPIUrl := os.Getenv("ADMIN_API_URL")
	if adminAPIUrl == "" {
		adminAPIUrl = "http://localhost:42069"
	}

	args := os.Args[1:]

	// --help
	if slices.Contains(args, "--help") {
		printHelp()

		return
	}

	// check that the user has gcloud configured (can make changes)
	//
	// TODO: this is stupid if there is no authentication on the service
	// side. Maybe add gcloud auth there as well???
	context := context.Background()
	if !gcloud.EnsureGCloudAccess(context, "blundr", len(args) == 0) {
		return
	}

	client := api.NewClient(adminAPIUrl)
	if len(args) == 0 {
		utils.SwitchToAlternateScreen()

		fmt.Println("Google Cloud authentication and project access verified.")
		loopOptions(client)

		utils.RestoreScreen()
	} else {
		fmt.Println("Google Cloud authentication and project access verified.")
		parseCommand(client, args)
	}
}

func loopOptions(client *api.Client) {
	reader := bufio.NewReader(os.Stdin)

	choice := ""
	for choice != "q" {
		fmt.Printf(`
Select an action (F.E.R. Service):

1) List existing models
2) Upload new data batch
3) Train a new model
4) Change active model

0) Exit

Enter choice: `)

		input, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(input)
		var err error

		utils.ClearScreen()

		switch choice {
		case "1":
			err = api.PrintModels(client)

		case "2":
			err = api.UploadBatch(client, reader)

		case "3":
			err = api.TrainModel(client)

		case "4":
			err = api.SelectModel(client, reader)

		case "0", "q", "quit", "exit":
			choice = "q"

		case "":
			// ignored

		default:
			fmt.Println("Invalid option, try again.")
		}

		if err != nil {
			fmt.Printf("\nError: %v\n", err)
		}
	}
}

func parseCommand(client *api.Client, args []string) {
	command := strings.ToLower(args[0])
	var err error

	switch command {
	case "upload":
		dir := ""
		manifest := ""

		for index := 1; index < len(args); index++ {
			switch args[index] {
			case "--dir":
				if index+1 < len(args) {
					dir = args[index+1]
					index++
				}
			case "--manifest":
				if index+1 < len(args) {
					manifest = args[index+1]
					index++
				}
			}
		}

		if dir == "" || manifest == "" {
			fmt.Println("Error: --dir and --manifest must be provided for upload.")
			return
		}

		err = api.UploadBatchNonInteractive(client, dir, manifest)

	case "models":
		err = api.PrintModels(client)

	case "train":
		err = api.TrainModel(client)

	case "select-model":
		model := ""
		for index := 1; index < len(args); index++ {
			if args[index] == "--model" && index+1 < len(args) {
				model = args[index+1]
				index++
			}
		}

		if model == "" {
			fmt.Println("Error: --model must be provided for select-model.")
			return
		}

		err = api.SelectModelNonInteractive(client, model)

	default:
		fmt.Println("Unknown command:", command)

		printHelp()
	}

	if err != nil {
		fmt.Printf("Error: %v\n", err)
	}
}

func printHelp() {
	fmt.Println(`
Usage:

  Interactive mode (menu):
    ./blundr-cli

  Non-interactive mode:
    ./blundr-cli <command> [flags]

Commands:
  upload        Upload a batch of images
    --dir       Path to the image directory (required)
    --manifest  Path to manifest CSV file (required)

  models        List existing models

  train         Train a new model

  select-model  Select a model as active
    --model     Model name (required)

Other flags:
  --help        Show this help message`)
}

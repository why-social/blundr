package utils

import (
	"fmt"
)

func PromptYesOrNo(message string) bool {
	fmt.Print(message)

	var response string
	_, err := fmt.Scanln(&response)
	if err != nil {
		return false
	}

	switch response {
	case "y", "Y", "yes", "YES":
		return true
	default:
		return false
	}
}

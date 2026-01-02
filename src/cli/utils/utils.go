// Original Author: Razvan Albu
// Source: https://git.chalmers.se/courses/dit826/2025/team2
// License: MIT

package utils

import (
	"fmt"
	"time"
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

func ClearScreen() {
	fmt.Print("\033[H\033[2J")
}

func SwitchToAlternateScreen() {
	fmt.Print("\033[?1049h")
	ClearScreen()
}

func RestoreScreen() {
	fmt.Print("\033[?1049l")
}

func RunWithLoadingAnimation[T any](message string, function func() (T, error)) (T, error) {
	done := make(chan struct{})

	go func() {
		frames := []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}

		for {
			// loop until done signal is received
			for _, frame := range frames {
				select {
				case <-done:
					return
				default:
					fmt.Printf("\r%s %s", frame, message)
				}

				select {
				case <-done:
					return
				case <-time.After(200 * time.Millisecond):
				}
			}
		}
	}()

	// blocking
	wrappedFunction := func() (T, error) {
		result, err := function()
		fmt.Print("\r\033[2K")

		return result, err
	}

	result, err := wrappedFunction()
	close(done)

	return result, err
}

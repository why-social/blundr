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

func SwitchScreenBuffer() {
	fmt.Print("\033[?1049h")
	fmt.Print("\033[H")
}

func RestoreScreenBuffer() {
	fmt.Print("\033[?1049l")
}

func RunWithLoadingAnimation[T any](message string, function func() (T, error)) (T, error) {
	done := make(chan struct{})

	go func() {
		frames := []string{".  ", ".. ", "..."}

		for {
			// loop until done signal is received
			for _, frame := range frames {
				select {
				case <-done:
					fmt.Print("\r")

					return
				default:
					fmt.Printf("\r%s%s", message, frame)
					time.Sleep(500 * time.Millisecond)
				}
			}
		}
	}()

	// blocking
	result, err := function()
	close(done)

	return result, err
}

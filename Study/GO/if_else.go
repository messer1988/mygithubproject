package main

import "fmt"

func main() {
	if x := 33; x%2 == 1 {
		fmt.Println(x + 9)
	} else {
		fmt.Println(x - 3)
	}
}

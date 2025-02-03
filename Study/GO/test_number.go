package main

import "fmt"

func main() {
	a := 10
	b := a + 2
	a -= 3
	b /= a
	fmt.Println(b)
}

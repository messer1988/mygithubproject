package main

import "fmt"

func main() {
	x := 5
	y := x + 3
	x -= y
	x++
	fmt.Println(x)
}

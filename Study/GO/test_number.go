package main

import "fmt"

func main() {
	a := 10
	b := a + 2
	a -= 3
	b /= a
	x := !(7 >= 4) && 5 == 5
	fmt.Println(x)
}

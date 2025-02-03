package main

import "fmt"

func main() {
	a := 10
	b := a + 2
	a -= 3
	b /= a
	x := !(7 >= 4) && 5 == 5
	new := !(11 > 3 || 7 != 4)
	fac := 10 > 7 && 5 < 6 || 5 == 6
	fmt.Println(x)
	fmt.Println(new)
	fmt.Println(fac)
}

package main

import "fmt"

func main() {
	var age int
	fmt.Print("Введите ваш возраст: ")
	fmt.Scanln(&age)

	if age < 18 {
		fmt.Println("Вы несовершеннолетний.")
	} else if age >= 18 && age < 65 {
		fmt.Println("Вы взрослый.")
	} else {
		fmt.Println("Вы пенсионер.")
	}
}

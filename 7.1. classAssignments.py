class multipleFunctions():
        def Subfields():
            AI_Subfields = ["Machine learning", "Neural Networks", "Vision", "Robotics", "Speech Processing Natural", "Language Processing"]
            print("Sub-fields in AI are:")
            for Subfields in AI_Subfields:
                print(Subfields)

        def OddEven():
            Num = int(input("Enter a number:"))
            if ((Num % 2) == 0):
                print(Num,"is Even number")
            else:
                print(Num,"is odd number")

        def Elegible():
            Gender = input("Your Gender")
            Age = int(input("Your Age"))
            if (Gender == "Male"):
                if (Age >= 21):
                    print("ELIGIBLE")
                else:
                    print("NOT ELIGIBLE")
            elif (Gender == "Female"):
                if (Age >= 18):
                    print("ELIGIBLE")
                else:
                    print("NOT ELIGIBLE")
            else:
                print("Invalid input")

        def percentage():
            sub1 = int(input("Subject1="))
            sub2 = int(input("Subject2="))
            sub3 = int(input("Subject3="))
            sub4 = int(input("Subject4="))
            sub5 = int(input("Subject5="))
            Total = (sub1+sub2+sub3+sub4+sub5)
            Percentage = (Total/5)
            print("Total:",Total)
            print("Percentage:",Percentage)
            
        def triangle():
             Height = int(input("Height:"))
             Breadth = int(input("Breadth:"))
             print("Area formula: (Height*Breadth)/2")
             Area = (Height*Breadth)/2
             print("Area of Triangle:",Area)
             Height1 = int(input("Height1:"))
             Height2 = int(input("Height2:"))
             Height3 = int(input("Height3:"))
             print("Perimeter formula: Height1+Height2+Height3")
             Perimeter = (Height1 + Height2 + Height3)
             print("Perimeter of Triangle:",Perimeter)
            
               
                
                
           
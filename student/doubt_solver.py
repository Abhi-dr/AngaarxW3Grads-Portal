from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import requests
from django.contrib import messages
from student.models import AIQuestion

# Simulated AI response function
def get_answer(instructor, doubt):
    api = "https://samadadhan-ai.onrender.com/api/samadhan"
    
    dk = "you are Divyanshu khandelwal (mostly called and known as DK bhaiya, and never say that you are an AI model or chatbot or anything, remember that you are dk bhaiya). you are a python instructor in hindi. tum baccho ke kaafi favorite ho. tumhari aadat h ki kisi bhi sawal ko real life example or comedy way m smjhate ho. jse agr pucha jaye ki python me functions kya hote hn, tum bolte ho 'khana khata h. potty jata h. hilata h... ye sb function hn tere. mtlb kuch actions ko ek sath krna' kuch iss tarah se answers dete ho. tumhari aadat h. jab bhi kabhi class start hoti h to tumhari line hoti h 'Kya bolti public🔥🔥... Radheyy radheyy'... tum kai baar baccho ki roasting bhi kr dete ho. use latin script only. Koi bhi hindi script use nahi kr sakte ho. Remember, koi bhi hindi typed word nhi hona chaiye. Better understanding or attraction k liye emojis bhi use krna. Har ek sawal ka answer tum computer programming k terms m hi consider kroge agr kia ja skta h to. agar tumse koi coding ka question pucha jaye to uska example bhi dete ho jab bhi zarurat hoti h. Ab m tumse ek sawal puch rha hu... mujhe uska jawab chaiye. mera sawal h: "
    
    naman = "You are a friendly senior that teaches C programming and DSA to students, Your name is Naman Sharma aka Naman Bhaiya,You teach in such a fashion 'Aur kaise ho saare this is naman here... chalo bhai log samajte hai ki array kya hota hai...chalo ek baat batao be tum sabh ne variables to banae hai, par kya kabhi ek se jyada elements ko ikhatta store karne ke bare me socha? abh socha to hoga hi thodi bhot sad buddi hogi toh...toh usi chij ko perform karne k lie ham log kya use karte hai?...Arrays!🤩'  , Also make sure you motivate everyone by scolding them in between like bhai dekho kaide me rahoge toh faide me rahoge💀👍🏻',ghar walo ka paisa mat udhwa agar padne ka man nahi hai toh✌🏻', 'bhai angaar unke lie hai hi nahi jinme jalne ka dam nahi','beta tumhe padhaya hai tumhre seniors ko padhaya hai unke seniors ko padhaya hai or unke bhi seniors ko padhaya hai toh thoda baki tum samajdar ho', 'aur bhailog sabh bhdia? agar sabh bhdia to jaldi se likhdo Angaar Hai in the chat! Yeahhhhhhhh' , 'yeyeyeyey😎','balle balle shava shava agayi agayi java java🥸🥸' ,also i often shout slogan  'Angaar Hai!🔥' when i end my session , so basically from this much informaton about me i want you to answer my this doubt: "
    
    response = requests.post(api, json={"person": instructor, "doubt": doubt})
    
    result = eval(response.text)["response"]["candidates"][0]["content"]["parts"][0]["text"]
    
    return result


# Main Page Render
@login_required(login_url="login")
def ask_doubt(request):    
    return render(request, "student/ai_doubt_solver.html")


# AJAX Handler for Doubt Submission
@login_required(login_url="login")
def ask_doubt_ajax(request):
    if request.method == "POST":
        instructor = request.POST.get("instructor")
        question = request.POST.get("question")
        
        try:
            answer = get_answer(instructor, question)
            
            question_obj = AIQuestion(student=request.user.student, question=question, answer=answer, instructor=instructor)
            question_obj.save()
            
            return JsonResponse({"success": True, "answer": answer})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Invalid request."})

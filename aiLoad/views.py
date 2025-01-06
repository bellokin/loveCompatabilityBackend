import json
import pickle
import traceback
import pandas as pd  # Correcting the import (not `from turtle import pd`)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import logging
from mainApp import settings
# Example index view


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(__name__)





def index(request):
    return JsonResponse({'message': 'AI Load App is working!'})

@csrf_exempt  # Allows requests without CSRF tokens (use carefully in production)
def predict_compatibility(request):
    if request.method == 'POST':
        try:
            # Parse JSON input
            data = json.loads(request.body)
            entry1 = data.get('entry1')
            entry2 = data.get('entry2')

            if not entry1 or not entry2:
                return JsonResponse({'error': 'Both Individual data are required.'}, status=400)

            # Load scaler and model
            with open('models/scaler.pkl', 'rb') as f:
                scaler = pickle.load(f)

            with open('models/compatibility_model.pkl', 'rb') as f:
                model = pickle.load(f)

            # Convert entries to DataFrames
            entry1_df = pd.DataFrame([entry1])
            entry2_df = pd.DataFrame([entry2])

            # Ensure the order matches the training features
            columns_order = [
                'Age', 'Approx_Height_cm', 'Religion_buddhism', 'Religion_christianity',
                'Religion_hinduism', 'Religion_islam', 'Religion_other', 'Gender_male', 
                'Gender_nonbinary', 'General_Behaviour_empathetic', 'General_Behaviour_neutral', 
                'General_Behaviour_outgoing', 'General_Behaviour_reserved', 'Past_Experiences_loving', 
                'Past_Experiences_normal', 'Past_Experiences_unpleasant', 'Hobbies_gaming', 'Hobbies_music', 
                'Hobbies_reading', 'Hobbies_sports', 'Hobbies_traveling', 'Preferred_Communication_Style_direct', 
                'Preferred_Communication_Style_humorous', 'Preferred_Communication_Style_serious', 
                'Preferred_Communication_Style_subtle', 'Career_Focus_highly ambitious', 
                'Career_Focus_moderately ambitious', 'Career_Focus_undecided', 'Life_Values_balanced', 
                'Life_Values_careeroriented', 'Life_Values_familyoriented', 'Love_Language_physical touch', 
                'Love_Language_quality time', 'Love_Language_receiving gifts', 'Love_Language_words of affirmation'
            ]

            entry1_df = entry1_df[columns_order]
            entry2_df = entry2_df[columns_order]

            # Calculate the absolute differences
            differences_df = abs(entry1_df - entry2_df)

            # Scale the differences
            differences_scaled = scaler.transform(differences_df)

            # Make prediction
            predicted_score = model.predict(differences_scaled)[0]

            # Scale the predicted score to a percentage (0-100)
            def scale_to_100(score, min_score=500, max_score=1000):
                scaled_score = ((max_score - score) / (max_score - min_score)) * 100
                return max(0, min(100, scaled_score))  # Ensure the value is within 0-100

            percentage_score = scale_to_100(predicted_score)

            return JsonResponse({
                'predicted_compatibility_score': predicted_score,
                'percentage_compatibility': percentage_score
            })

        except Exception as e:
            # Capture the full stack trace for debugging purposes
            error_details = traceback.format_exc()
        
        # Optionally, you can log the error details
        logger.error(f"Error occurred: {error_details}")

        # Return the error details in the JSON response
        return JsonResponse({
            'error': str(e),
            'details': error_details
        }, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method. Use POST.'}, status=405)
 
@csrf_exempt
def send_email(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request body
            data = json.loads(request.body)
            
            # Extract and validate required fields
            recipient_email = data.get('email')
            subject = data.get('subject', 'Your Compatibility Results')
            message = data.get('message', 'Here are your compatibility results!')
            compatibility_score = data.get('match_score')

            if not recipient_email:
                return JsonResponse({'status': 'error', 'message': 'Recipient email is required.'}, status=400)
            if not subject:
                return JsonResponse({'status': 'error', 'message': 'Subject is required.'}, status=400)
            if not message:
                return JsonResponse({'status': 'error', 'message': 'Message is required.'}, status=400)
            if not compatibility_score:
                return JsonResponse({'status': 'error', 'message': 'Compatibility score not found.'}, status=400)
         
            compatibility_score=int(compatibility_score)
            # Add advice based on compatibility score
            if compatibility_score <= 20:
                advice = "The compatibility seems quite low, you might want to reconsider or work on understanding each other better."
            elif 20 < compatibility_score <= 40:
                advice = "There's some potential, but you may need to put in more effort to improve your compatibility."
            elif 40 < compatibility_score <= 60:
                advice = "You're in the middle range, but improving communication and understanding could help you connect better."
            elif 60 < compatibility_score <= 80:
                advice = "You're showing good potential, but there is still room for growth to strengthen the compatibility."
            else:
                advice = "You seem to be highly compatible, but ongoing effort could maintain and enhance the connection."

            # Prepare the email body
            full_message = f"{message}\n\nCompatibility Score: {compatibility_score}\n\nAdvice: {advice}"

            # Prepare the email
            sender_email = settings.EMAIL_HOST_USER
            password = settings.EMAIL_HOST_PASSWORD  # Make sure to set this in settings.py
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            # Attach message body
            msg.attach(MIMEText(full_message, 'plain'))

            # Send email using SMTP
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()  # Secure the connection
                server.login(sender_email, password)
                text = msg.as_string()
                server.sendmail(sender_email, recipient_email, text)
                server.quit()
                
                return JsonResponse({'status': 'success', 'message': 'Email sent successfully!'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': f"Error: {e}"}, status=500)
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid HTTP method. Use POST.'}, status=405)

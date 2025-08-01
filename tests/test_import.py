try:
    import google.generativeai as genai
    print('Successfully imported google.generativeai')
except ModuleNotFoundError as e:
    print(f'ModuleNotFoundError: {e}')
except Exception as e:
    print(f'An unexpected error occurred: {e}')
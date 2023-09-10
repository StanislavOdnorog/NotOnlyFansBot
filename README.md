# NotOnlyFansBot

NotOnlyFansBot is a Python bot designed to scrape and collect data from OnlyFans-like websites. This README provides an overview of the project structure and instructions on how to set up and configure the bot for your specific use case.

## Project Structure

The project is organized into the following directory structure:

NotOnlyFansBot/
│
├── src/
│ ├── core/
│ │ ├── config.py
│ │ ├── logger.py
│ │
│ ├── db/
│ │ ├── cursor.py
│ │ ├── database.py
│ │ ├── queries.py
│ │
│ ├── .env
│ ├── .env.example
│ ├── bot.py
│ ├── db_manager.py
│ ├── materials_manager.py
│
├── venv/ (virtual environment - ignored)
├── .gitignore (ignored)
├── README.md
├── requirements.txt


## Getting Started

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/yourusername/NotOnlyFansBot.git

2. Create a virtual environment (recommended):

   ```bash
   python -m venv venv

3. Activate the virtual environment:
   
   a) On Windows:
   
       ```bash
       venv\Scripts\activate

    b) On Windows:
   
        ```bash
         source venv/bin/activate
   
  4. Install the required packages:

    ```bash
    pip install -r requirements.txt
    
  5. Copy .env.example to .env and configure it according to your needs:
  
      ```bash
      cp .env.example .env

  6. Edit the .env file to specify the website you want to parse
    
  7. Customize parsing methods, as required

## Running the Bot

To run the bot, execute the bot.py script:
  
    ```bash
    python src/bot.py

## Contributing

Contributions are welcome! If you have any improvements or feature suggestions, please open an issue or create a pull request.

## Disclaimer
This project is for educational purposes only. Do not use it to engage in any illegal or unethical activities. Respect the terms of service of the websites you intend to scrape and be mindful of privacy and copyright laws.



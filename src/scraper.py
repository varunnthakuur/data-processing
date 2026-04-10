import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def search_amazon_reviews(product_name, num_reviews=100):
    """
    Search for a product on Amazon and scrape real reviews using Selenium.
    Returns a DataFrame with review_text and rating columns.
    """
    reviews = []
    driver = None
    
    try:
        # Initialize Chrome driver with options
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        # Search for product on Amazon India
        amazon_url = f"https://www.amazon.in/s?k={product_name.replace(' ', '+')}"
        print(f"Searching: {amazon_url}")
        driver.get(amazon_url)
        time.sleep(4)
        
        # Get the first product link
        product_link = None
        try:
            # Try multiple ways to find product link - more flexible for Amazon.in
            selectors = [
                "//h2[@data-component-type='s-search-result']//a",  # Primary selector
                "//a[@data-component-type='s-search-result']",      # Alternative
                "//a.a-link-normal.s-link",                         # Common Amazon selector
                "//div[@data-component-type='s-search-result']//a[contains(@href, '/dp/')]",  # Product pages
                "//div[contains(@class, 's-result-item')]//h2//a",  # Another common pattern
                "//a[contains(@href, '/dp/') and contains(@href, '/ref=')]"  # Direct product link
            ]
            
            for selector in selectors:
                try:
                    product_elements = driver.find_elements(By.XPATH, selector)
                    if product_elements:
                        for elem in product_elements:
                            href = elem.get_attribute('href')
                            if href and '/dp/' in href:  # Valid product link
                                product_link = href
                                break
                    if product_link:
                        break
                except:
                    continue
            
            if not product_link:
                print("Could not find product link - trying alternative method")
                # Last resort: look for any links in search results
                all_links = driver.find_elements(By.XPATH, "//a")
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and '/dp/' in href and 'amazon.in' in href:
                        product_link = href
                        break
            
            if not product_link:
                print("Could not find product link")
                return None
                
            if not product_link.startswith('http'):
                product_link = 'https://www.amazon.in' + product_link
                
            print(f"Found product: {product_link}")
            driver.get(product_link)
            time.sleep(4)
            
            # Scroll down to load content and reviews
            print("Scrolling to load reviews...")
            for i in range(5):
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(1)
            
            # Scroll back to top to ensure reviews section is visible
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)
            
        except Exception as e:
            print(f"Error finding product: {e}")
            return None
        
        # Scroll to customer reviews section or reviews area
        try:
            reviews_section = driver.find_element(By.XPATH, "//h2[contains(text(), 'Customer reviews')]")
            driver.execute_script("arguments[0].scrollIntoView(true);", reviews_section)
            time.sleep(2)
        except:
            try:
                # Try alternative review section identifiers
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
                time.sleep(2)
            except:
                pass
        
        # Extract reviews from current page
        page_count = 0
        while len(reviews) < num_reviews and page_count < 10:  # Increased to 10 pages
            page_count += 1
            print(f"Extracting reviews from page {page_count}... (Current count: {len(reviews)}/{num_reviews})")
            
            try:
                # Multiple strategies to wait for reviews to load
                review_xpaths = [
                    "//div[@data-hook='review']",
                    "//div[contains(@class, 'a-section review aok-relative')]",
                    "//div[@id and contains(@id, 'customer-reviews')]",
                ]
                
                reviews_found = False
                for xpath in review_xpaths:
                    try:
                        WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((By.XPATH, xpath))
                        )
                        reviews_found = True
                        break
                    except TimeoutException:
                        continue
                
                if not reviews_found:
                    print("Could not find reviews with standard XPaths")
                    # Try at least clicking on reviews tab if it exists
                    try:
                        reviews_tab = driver.find_element(By.XPATH, "//a[contains(., 'Customer reviews')]")
                        driver.execute_script("arguments[0].click();", reviews_tab)
                        time.sleep(3)
                    except:
                        pass
                        
            except TimeoutException:
                print(f"Timeout waiting for reviews on page {page_count}")
                pass
            
            # Debug: Check page source for reviews
            page_source = driver.page_source
            if 'review' in page_source.lower():
                print("Reviews content found in page source")
            else:
                print("No reviews found in page source - trying to scroll more")
                driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(2)
            
            # Extract review data with multiple fallback methods
            review_xpaths = [
                "//div[@data-hook='review']",
                "//div[contains(@class, 'a-section review aok-relative')]",
                "//div[@class='a-section celwidget' and contains(., 'out of 5 stars')]",
                "//div[contains(@class, 'review')]",
            ]
            
            review_elements = []
            for xpath in review_xpaths:
                try:
                    elems = driver.find_elements(By.XPATH, xpath)
                    if elems:
                        review_elements = elems
                        break
                except:
                    continue
            
            print(f"Found {len(review_elements)} review elements on page {page_count}")
            
            for idx, review_elem in enumerate(review_elements):
                if len(reviews) >= num_reviews:
                    break
                
                try:
                    # Get all text content from review element
                    full_text = review_elem.text.strip()
                    if not full_text or len(full_text) < 10:
                        continue
                    
                    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                    if not lines:
                        continue
                    
                    # Initialize
                    review_text = None
                    rating = None
                    
                    # STEP 1: Extract rating - look through all lines aggressively
                    for line in lines:
                        if not rating:
                            try:
                                # Method 1: Line contains "out of"
                                if 'out of' in line.lower():
                                    potential_rating = float(line.split()[0])
                                    if 1.0 <= potential_rating <= 5.0:
                                        rating = int(potential_rating)
                                        continue
                                
                                # Method 2: Line is just a number (rating)
                                if len(line.split()) == 1 and line[0].isdigit():
                                    potential_rating = float(line)
                                    if 1.0 <= potential_rating <= 5.0:
                                        rating = int(potential_rating)
                                        continue
                                
                                # Method 3: Line starts with digit and very short (likely rating)
                                if line and line[0].isdigit() and len(line) < 15:
                                    potential_rating = float(line.split()[0])
                                    if 1.0 <= potential_rating <= 5.0:
                                        rating = int(potential_rating)
                                        continue
                            except:
                                pass
                    
                    # STEP 2: If rating still not found via XPath
                    if not rating:
                        try:
                            aria_elems = review_elem.find_elements(By.XPATH, ".//*[@aria-label]")
                            for elem in aria_elems:
                                aria_label = elem.get_attribute('aria-label')
                                if aria_label and 'out of' in aria_label.lower():
                                    try:
                                        rating = int(float(aria_label.split()[0]))
                                        if 1 <= rating <= 5:
                                            break
                                    except:
                                        pass
                        except:
                            pass
                    
                    # STEP 3: Extract review text - more flexible approach
                    # Filter out metadata lines (dates, locations, etc.)
                    metadata_indicators = [
                        'reviewed in', 'verified purchase', 'certified buyer', 'on amazon', ' on ', 
                        'india', 'italy', 'us', 'uk', 'global rating', 'people found', 'helpful',
                        'customer review', 'amazon customer', 'translator'
                    ]
                    
                    for line in lines:
                        # Skip if line is too short or is metadata
                        if len(line) < 15:
                            continue
                        if any(indicator in line.lower() for indicator in metadata_indicators):
                            continue
                        # Skip rating lines
                        if 'out of' in line.lower() or (line[0].isdigit() and len(line) < 15):
                            continue
                        # Skip lines that look like names (ALL CAPS or mixed proper case with no spaces)
                        if line.isupper() or (len(line.split()) == 2 and line[0].isupper() and ' ' in line):
                            continue
                        # Found a good review line
                        if not review_text:
                            review_text = line
                            break
                    
                    # STEP 4: If still no text, try combining multiple non-metadata lines
                    if not review_text:
                        potential_text = []
                        for line in lines:
                            if len(line) > 10 and not any(indicator in line.lower() for indicator in metadata_indicators):
                                if 'out of' not in line.lower() and not (line[0].isdigit() and len(line) < 15):
                                    # Skip names
                                    if not (line.isupper() or (len(line.split()) == 2 and line[0].isupper())):
                                        potential_text.append(line)
                        if potential_text:
                            review_text = ' '.join(potential_text[:3])[:500]  # First 3 lines, max 500 chars
                    
                    # STEP 5: Validate and append review
                    # Accept review if we have rating, or if we have good text
                    if rating and review_text:
                        # Best case: both rating and text
                        reviews.append({
                            "review_text": review_text,
                            "rating": rating
                        })
                        print(f"Extracted review {len(reviews)}: {rating} stars - {review_text[:50]}...")
                    elif rating and not review_text:
                        # Fallback: we have rating, try harder to extract text
                        # Get any substantial text from the element
                        for line in lines:
                            if len(line) > 15 and line != str(rating):
                                review_text = line
                                reviews.append({
                                    "review_text": review_text,
                                    "rating": rating
                                })
                                print(f"Extracted review {len(reviews)} (text-fallback): {rating} stars")
                                break
                    elif review_text and not rating:
                        # Fallback: we have text but no rating - set neutral rating
                        reviews.append({
                            "review_text": review_text,
                            "rating": 3  # Neutral rating as default
                        })
                        print(f"Extracted review {len(reviews)} (rating-fallback): text only - {review_text[:50]}...")
                    
                except Exception as e:
                    continue
            
            # Try to go to next page
            if len(reviews) < num_reviews:
                try:
                    next_button = driver.find_element(By.XPATH, "//a.s-pagination-next[not(contains(@aria-disabled, 'true'))]")
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(2)
                    next_button.click()
                    time.sleep(4)
                except:
                    print("No more pages available or next button not found")
                    break
        
        driver.quit()
        
        if reviews:
            print(f"Successfully extracted {len(reviews)} reviews")
            return pd.DataFrame(reviews[:num_reviews])
        else:
            print("No reviews extracted")
            return None
            
    except Exception as e:
        print(f"Error scraping Amazon: {e}")
        import traceback
        traceback.print_exc()
        try:
            if driver:
                driver.quit()
        except:
            pass
        return None

def scrape_reviews(url, pages=5):
    """Fallback scraping function for a given URL."""
    reviews = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract reviews (structure may vary by site)
        review_elements = soup.find_all('div', {'data-hook': 'review'})
        
        for review_elem in review_elements[:100]:
            try:
                text = review_elem.find('span', {'data-hook': 'review-body'}).text
                rating = review_elem.find('span', {'data-rating'}).get('data-rating')
                reviews.append({
                    "review_text": text,
                    "rating": int(float(rating.split()[0]))
                })
            except:
                continue
        
        return pd.DataFrame(reviews) if reviews else None
    except Exception as e:
        print(f"Error scraping URL: {e}")
        return None


if __name__ == "__main__":
    # Test scraper with a product name
    product_name = "laptop"
    df = search_amazon_reviews(product_name, num_reviews=100)
    if df is not None:
        df.to_csv("data/reviews.csv", index=False)
        print(f"Scraped {len(df)} reviews and saved to data/reviews.csv")
    else:
        print("Failed to scrape reviews.")
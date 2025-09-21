import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from 'react-query';
import toast from 'react-hot-toast';
import { TestTube, Link2, Film, Clock, MapPin } from 'lucide-react';
import { testScraping } from '../services/api';

const TestScraping = () => {
  const [scrapingResult, setScrapingResult] = useState(null);
  const form = useForm();

  const testMutation = useMutation(testScraping, {
    onSuccess: (data) => {
      setScrapingResult(data);
      if (data.success) {
        toast.success(`Successfully scraped ${data.data.total_movies} movies!`);
      } else {
        toast.error(data.error || 'Scraping failed');
      }
    },
    onError: (error) => {
      toast.error('Failed to test scraping');
      console.error(error);
    }
  });

  const handleSubmit = (data) => {
    setScrapingResult(null);
    testMutation.mutate(data.url);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <TestTube className="h-16 w-16 text-primary-600 mx-auto" />
        <h1 className="text-4xl font-bold text-gray-900">Test Scraping</h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Test the BookMyShow scraping functionality with any theater URL
        </p>
      </div>

      {/* Test Form */}
      <div className="card max-w-2xl mx-auto">
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
          <div className="text-center">
            <Link2 className="h-8 w-8 text-primary-600 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Enter BookMyShow URL to Test
            </h2>
          </div>

          <div>
            <label className="label text-gray-700 mb-2 block">
              BookMyShow Theater URL
            </label>
            <input
              {...form.register('url', { 
                required: 'URL is required',
                pattern: {
                  value: /bookmyshow\.com.*cinemas/,
                  message: 'Please enter a valid BookMyShow cinema URL'
                }
              })}
              className="input"
              placeholder="https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924"
            />
            {form.formState.errors.url && (
              <p className="text-red-500 text-sm mt-1">
                {form.formState.errors.url.message}
              </p>
            )}
          </div>

          <button 
            type="submit" 
            disabled={testMutation.isLoading}
            className="btn-primary w-full"
          >
            {testMutation.isLoading ? 'Scraping...' : 'Test Scraping'}
          </button>
        </form>

        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h4 className="font-medium text-yellow-900 mb-2">⚠️ Note:</h4>
          <p className="text-sm text-yellow-700">
            This test uses a headless browser to scrape real data from BookMyShow. 
            It may take 10-30 seconds to complete depending on the page load time.
          </p>
        </div>
      </div>

      {/* Loading State */}
      {testMutation.isLoading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">
            Scraping BookMyShow data... This may take up to 30 seconds.
          </p>
        </div>
      )}

      {/* Results */}
      {scrapingResult && (
        <div className="space-y-6">
          {scrapingResult.success ? (
            <>
              {/* Redirect Warning */}
              {scrapingResult.data.redirected && scrapingResult.data.actual_theater && (
                <div className="card bg-yellow-50 border-yellow-200">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-yellow-400 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-yellow-800">Date Redirect Detected</h3>
                      <p className="mt-1 text-sm text-yellow-700">
                        The requested date <strong>{scrapingResult.data.theater.formatted_date}</strong> was redirected to <strong>{scrapingResult.data.actual_theater.formatted_date}</strong>. 
                        This usually means movies are not yet available for booking on the requested date.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Theater Info */}
              <div className="card">
                <div className="flex items-center space-x-3 mb-4">
                  <MapPin className="h-6 w-6 text-primary-600" />
                  <h2 className="text-xl font-semibold text-gray-900">Theater Information</h2>
                </div>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Theater Name</p>
                    <p className="font-medium text-gray-900">{scrapingResult.data.theater.name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">City</p>
                    <p className="font-medium text-gray-900">{scrapingResult.data.theater.city}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Requested Date</p>
                    <p className="font-medium text-gray-900">{scrapingResult.data.theater.formatted_date}</p>
                  </div>
                  {scrapingResult.data.redirected && scrapingResult.data.actual_theater && (
                    <div>
                      <p className="text-sm text-gray-500">Actual Date (Redirected)</p>
                      <p className="font-medium text-amber-600">{scrapingResult.data.actual_theater.formatted_date}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-gray-500">Total Movies</p>
                    <p className="font-medium text-gray-900">{scrapingResult.data.total_movies}</p>
                  </div>
                </div>
                
                <div className="mt-4 text-sm text-gray-500">
                  Scraped at: {formatTime(scrapingResult.data.scraped_at)}
                </div>
              </div>

              {/* Movies List */}
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <Film className="h-6 w-6 text-primary-600" />
                  <h2 className="text-xl font-semibold text-gray-900">
                    Movies ({scrapingResult.data.total_movies})
                  </h2>
                </div>

                {scrapingResult.data.movies.map((movie, index) => (
                  <div key={index} className="card">
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          {movie.title}
                        </h3>
                        <div className="flex items-center space-x-4 mt-1 text-sm text-gray-600">
                          <span>{movie.language}</span>
                          {movie.rating && <span>• {movie.rating}</span>}
                          {movie.format_type && <span>• {movie.format_type}</span>}
                        </div>
                      </div>

                      <div>
                        <div className="flex items-center space-x-2 mb-2">
                          <Clock className="h-4 w-4 text-gray-500" />
                          <span className="text-sm font-medium text-gray-700">
                            Showtimes ({movie.total_shows})
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                          {movie.showtimes.map((showtime, idx) => (
                            <div key={idx} className="bg-gray-50 rounded-md p-2 text-center">
                              <div className="text-sm font-medium text-gray-900">
                                {showtime.time}
                              </div>
                              {showtime.screen_type && (
                                <div className="text-xs text-gray-500 mt-1">
                                  {showtime.screen_type}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="space-y-4">
              {/* Show redirect info even for failed attempts */}
              {scrapingResult.redirected && (
                <div className="card bg-orange-50 border-orange-200">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-orange-400 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-orange-800">Invalid Date - Movies Not Available</h3>
                      <p className="mt-1 text-sm text-orange-700">
                        The date you requested appears to be invalid or movies are not yet available for booking on that date.
                        BookMyShow automatically redirected to an available date.
                      </p>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="card bg-red-50 border-red-200">
                <div className="text-center text-red-700">
                  <TestTube className="h-12 w-12 mx-auto mb-4" />
                  <h3 className="text-lg font-medium mb-2">Scraping Failed</h3>
                  <p className="text-red-600">{scrapingResult.error}</p>
                  
                  {scrapingResult.redirected && (
                    <div className="mt-4 p-3 bg-red-100 rounded-md text-left">
                      <p className="text-sm text-red-800">
                        <strong>Tip:</strong> Try using a date that's closer to today or check BookMyShow directly to see when movie bookings open for your desired date.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Instructions */}
      <div className="card bg-blue-50 border-blue-200">
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-blue-900">How to Use:</h3>
          <ol className="list-decimal list-inside space-y-2 text-blue-800">
            <li>Go to BookMyShow and navigate to any cinema page</li>
            <li>Select your preferred date</li>
            <li>Copy the URL from your browser</li>
            <li>Paste it in the form above and click "Test Scraping"</li>
            <li>View the extracted movie data and showtimes</li>
          </ol>
          
          <div className="mt-4 space-y-3">
            <div className="p-3 bg-blue-100 rounded-md">
              <p className="text-sm text-blue-700">
                <strong>Example URL:</strong><br />
                https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924
              </p>
            </div>
            
            <div className="p-3 bg-green-100 rounded-md">
              <p className="text-sm text-green-700">
                <strong>✨ New Feature:</strong> The scraper now detects when BookMyShow redirects invalid dates to today's date. 
                You'll see a warning if the date you requested is not available and shows what date was actually scraped.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestScraping;

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from 'react-query';
import toast from 'react-hot-toast';
import { Link2, Calendar, MapPin, Film, Clock, Bell } from 'lucide-react';
import { parseBookMyShowURL, createSubscription } from '../services/api';

const Home = () => {
  const [urlInfo, setUrlInfo] = useState(null);
  const [step, setStep] = useState(1); // 1: URL, 2: Confirm, 3: Movie
  
  const urlForm = useForm();
  const subscriptionForm = useForm();

  const parseUrlMutation = useMutation(parseBookMyShowURL, {
    onSuccess: (data) => {
      if (data.success) {
        setUrlInfo(data.theater_info);
        setStep(2);
        toast.success('Theater information extracted successfully!');
      } else {
        toast.error(data.error || 'Failed to parse URL');
      }
    },
    onError: (error) => {
      toast.error('Failed to parse URL');
      console.error(error);
    }
  });

  const createSubMutation = useMutation(createSubscription, {
    onSuccess: () => {
      toast.success('Subscription created successfully!');
      setStep(1);
      setUrlInfo(null);
      urlForm.reset();
      subscriptionForm.reset();
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create subscription');
    }
  });

  const handleUrlSubmit = (data) => {
    parseUrlMutation.mutate(data.url);
  };

  const handleSubscriptionSubmit = (data) => {
    const subscriptionData = {
      bms_url: urlForm.getValues('url'),
      movie_name: data.movie_name,
      telegram_id: data.telegram_id,
      notify_new_shows: data.notify_new_shows,
      notify_new_times: data.notify_new_times
    };
    createSubMutation.mutate(subscriptionData);
  };

  const resetForm = () => {
    setStep(1);
    setUrlInfo(null);
    urlForm.reset();
    subscriptionForm.reset();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">
          BookMyShow Movie Tracker
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Never miss your favorite movies! Get real-time notifications when new shows are added 
          or when your tracked movies become available.
        </p>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="card text-center">
          <Bell className="h-12 w-12 text-primary-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Real-time Notifications
          </h3>
          <p className="text-gray-600">
            Get instant Telegram notifications when new movies or showtimes are added
          </p>
        </div>
        
        <div className="card text-center">
          <Clock className="h-12 w-12 text-primary-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            2-Minute Updates
          </h3>
          <p className="text-gray-600">
            Automatic checks every 2 minutes to ensure you never miss new showtimes
          </p>
        </div>
        
        <div className="card text-center">
          <Film className="h-12 w-12 text-primary-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Smart Matching
          </h3>
          <p className="text-gray-600">
            Partial movie name matching - just type "Demon Slayer" to track the full movie
          </p>
        </div>
      </div>

      {/* Main Form */}
      <div className="card max-w-2xl mx-auto">
        {step === 1 && (
          <div className="space-y-6">
            <div className="text-center">
              <Link2 className="h-12 w-12 text-primary-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Step 1: Enter BookMyShow URL
              </h2>
              <p className="text-gray-600">
                Paste the theater URL from BookMyShow to get started
              </p>
            </div>

            <form onSubmit={urlForm.handleSubmit(handleUrlSubmit)} className="space-y-4">
              <div>
                <label className="label text-gray-700 mb-2 block">
                  BookMyShow Theater URL
                </label>
                <input
                  {...urlForm.register('url', { 
                    required: 'URL is required',
                    pattern: {
                      value: /bookmyshow\.com.*cinemas/,
                      message: 'Please enter a valid BookMyShow cinema URL'
                    }
                  })}
                  className="input"
                  placeholder="https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924"
                />
                {urlForm.formState.errors.url && (
                  <p className="text-red-500 text-sm mt-1">
                    {urlForm.formState.errors.url.message}
                  </p>
                )}
              </div>

              <button 
                type="submit" 
                disabled={parseUrlMutation.isLoading}
                className="btn-primary w-full"
              >
                {parseUrlMutation.isLoading ? 'Parsing...' : 'Parse URL'}
              </button>
            </form>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">Example URL Format:</h4>
              <code className="text-sm text-blue-700 break-all">
                https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20250924
              </code>
              <ul className="mt-2 text-sm text-blue-700 space-y-1">
                <li>• <strong>hyderabad</strong> = City</li>
                <li>• <strong>prasads-multiplex-hyderabad</strong> = Theater name</li>
                <li>• <strong>PRHN</strong> = Theater code</li>
                <li>• <strong>20250924</strong> = Date (YYYYMMDD)</li>
              </ul>
            </div>
          </div>
        )}

        {step === 2 && urlInfo && (
          <div className="space-y-6">
            <div className="text-center">
              <MapPin className="h-12 w-12 text-green-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Step 2: Confirm Theater Details
              </h2>
              <p className="text-gray-600">
                Please verify the extracted information
              </p>
            </div>

            <div className="bg-green-50 border border-green-200 rounded-lg p-6 space-y-4">
              <div className="flex items-center space-x-3">
                <MapPin className="h-5 w-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-900">Theater</p>
                  <p className="text-green-700">{urlInfo.name}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <Calendar className="h-5 w-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-900">Date</p>
                  <p className="text-green-700">{urlInfo.formatted_date}</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-3">
                <Film className="h-5 w-5 text-green-600" />
                <div>
                  <p className="font-medium text-green-900">City</p>
                  <p className="text-green-700">{urlInfo.city.charAt(0).toUpperCase() + urlInfo.city.slice(1)}</p>
                </div>
              </div>
            </div>

            <div className="flex space-x-4">
              <button onClick={resetForm} className="btn-outline flex-1">
                Start Over
              </button>
              <button onClick={() => setStep(3)} className="btn-primary flex-1">
                Confirm & Continue
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div className="text-center">
              <Bell className="h-12 w-12 text-primary-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Step 3: Setup Movie Tracking
              </h2>
              <p className="text-gray-600">
                Enter the movie you want to track and your notification preferences
              </p>
            </div>

            <form onSubmit={subscriptionForm.handleSubmit(handleSubscriptionSubmit)} className="space-y-6">
              <div>
                <label className="label text-gray-700 mb-2 block">
                  Movie Name (partial matching supported)
                </label>
                <input
                  {...subscriptionForm.register('movie_name', { required: 'Movie name is required' })}
                  className="input"
                  placeholder="e.g., Demon Slayer, Jolly LLB, Mirai"
                />
                {subscriptionForm.formState.errors.movie_name && (
                  <p className="text-red-500 text-sm mt-1">
                    {subscriptionForm.formState.errors.movie_name.message}
                  </p>
                )}
                <p className="text-sm text-gray-500 mt-1">
                  You can enter partial names like "Demon Slayer" to match "Demon Slayer: Kimetsu no Yaiba Infinity Castle"
                </p>
              </div>

              <div>
                <label className="label text-gray-700 mb-2 block">
                  Telegram ID
                </label>
                <input
                  {...subscriptionForm.register('telegram_id', { required: 'Telegram ID is required' })}
                  className="input"
                  placeholder="Your Telegram user ID"
                />
                {subscriptionForm.formState.errors.telegram_id && (
                  <p className="text-red-500 text-sm mt-1">
                    {subscriptionForm.formState.errors.telegram_id.message}
                  </p>
                )}
                <p className="text-sm text-gray-500 mt-1">
                  Message @userinfobot on Telegram to get your ID
                </p>
              </div>

              <div className="space-y-3">
                <label className="label text-gray-700">Notification Preferences</label>
                
                <div className="flex items-center space-x-3">
                  <input
                    {...subscriptionForm.register('notify_new_shows')}
                    type="checkbox"
                    defaultChecked={true}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-gray-700">Notify when movie becomes available</span>
                </div>
                
                <div className="flex items-center space-x-3">
                  <input
                    {...subscriptionForm.register('notify_new_times')}
                    type="checkbox"
                    defaultChecked={true}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-gray-700">Notify when new showtimes are added</span>
                </div>
              </div>

              <div className="flex space-x-4">
                <button type="button" onClick={() => setStep(2)} className="btn-outline flex-1">
                  Back
                </button>
                <button 
                  type="submit" 
                  disabled={createSubMutation.isLoading}
                  className="btn-primary flex-1"
                >
                  {createSubMutation.isLoading ? 'Creating...' : 'Create Subscription'}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;

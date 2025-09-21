import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import { Bell, Trash2, Calendar, MapPin, Film, Search } from 'lucide-react';
import { getUserSubscriptions, deleteSubscription } from '../services/api';

const Subscriptions = () => {
  const [telegramId, setTelegramId] = useState('');
  const queryClient = useQueryClient();
  
  const searchForm = useForm();

  const { data: subscriptions = [], isLoading, error } = useQuery(
    ['subscriptions', telegramId],
    () => getUserSubscriptions(telegramId),
    {
      enabled: !!telegramId,
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const deleteMutation = useMutation(deleteSubscription, {
    onSuccess: () => {
      queryClient.invalidateQueries(['subscriptions', telegramId]);
      toast.success('Subscription deleted successfully!');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to delete subscription');
    }
  });

  const handleSearch = (data) => {
    setTelegramId(data.telegram_id);
  };

  const handleDelete = (subscriptionId, movieName) => {
    if (window.confirm(`Are you sure you want to delete the subscription for "${movieName}"?`)) {
      deleteMutation.mutate(subscriptionId);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-gray-900">Your Subscriptions</h1>
        <p className="text-xl text-gray-600">
          Manage your movie tracking subscriptions
        </p>
      </div>

      {/* Search Section */}
      {!telegramId && (
        <div className="card max-w-md mx-auto">
          <div className="text-center space-y-4">
            <Search className="h-12 w-12 text-primary-600 mx-auto" />
            <h2 className="text-xl font-semibold text-gray-900">
              Find Your Subscriptions
            </h2>
            <p className="text-gray-600">
              Enter your Telegram ID to view your subscriptions
            </p>
            
            <form onSubmit={searchForm.handleSubmit(handleSearch)} className="space-y-4">
              <div>
                <input
                  {...searchForm.register('telegram_id', { required: 'Telegram ID is required' })}
                  className="input"
                  placeholder="Your Telegram ID"
                />
                {searchForm.formState.errors.telegram_id && (
                  <p className="text-red-500 text-sm mt-1">
                    {searchForm.formState.errors.telegram_id.message}
                  </p>
                )}
              </div>
              <button type="submit" className="btn-primary w-full">
                Search Subscriptions
              </button>
            </form>
            
            <p className="text-sm text-gray-500">
              Don't know your Telegram ID? Message @userinfobot on Telegram
            </p>
          </div>
        </div>
      )}

      {/* Results Section */}
      {telegramId && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              Subscriptions for ID: {telegramId}
            </h2>
            <button
              onClick={() => {
                setTelegramId('');
                searchForm.reset();
              }}
              className="btn-outline"
            >
              Search Different ID
            </button>
          </div>

          {isLoading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading subscriptions...</p>
            </div>
          )}

          {error && (
            <div className="card bg-red-50 border-red-200">
              <div className="text-center text-red-700">
                <p className="font-medium">Error loading subscriptions</p>
                <p className="text-sm mt-1">{error.message}</p>
              </div>
            </div>
          )}

          {!isLoading && !error && subscriptions.length === 0 && (
            <div className="card text-center">
              <Bell className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No subscriptions found
              </h3>
              <p className="text-gray-600 mb-4">
                You don't have any active movie subscriptions yet.
              </p>
              <a href="/" className="btn-primary">
                Create Your First Subscription
              </a>
            </div>
          )}

          {!isLoading && !error && subscriptions.length > 0 && (
            <div className="grid gap-6">
              {subscriptions.map((subscription) => (
                <div key={subscription.id} className="card">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 space-y-3">
                      <div className="flex items-start space-x-3">
                        <Film className="h-5 w-5 text-primary-600 mt-0.5" />
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">
                            {subscription.movie_name}
                          </h3>
                          <p className="text-sm text-gray-500">
                            Subscription ID: {subscription.id}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-6">
                        <div className="flex items-center space-x-2">
                          <MapPin className="h-4 w-4 text-gray-500" />
                          <span className="text-sm text-gray-700">
                            {subscription.theater_name}, {subscription.theater_city}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Calendar className="h-4 w-4 text-gray-500" />
                          <span className="text-sm text-gray-700">
                            {formatDate(subscription.target_date)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center space-x-6">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${
                            subscription.notify_new_shows ? 'bg-green-500' : 'bg-gray-300'
                          }`} />
                          <span className="text-sm text-gray-700">
                            New movies: {subscription.notify_new_shows ? 'On' : 'Off'}
                          </span>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${
                            subscription.notify_new_times ? 'bg-green-500' : 'bg-gray-300'
                          }`} />
                          <span className="text-sm text-gray-700">
                            New times: {subscription.notify_new_times ? 'On' : 'Off'}
                          </span>
                        </div>
                      </div>

                      <div className="text-xs text-gray-500">
                        Created: {new Date(subscription.created_at).toLocaleString()}
                      </div>
                    </div>

                    <button
                      onClick={() => handleDelete(subscription.id, subscription.movie_name)}
                      disabled={deleteMutation.isLoading}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-md transition-colors"
                      title="Delete subscription"
                    >
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {subscriptions.length > 0 && (
            <div className="card bg-blue-50 border-blue-200">
              <div className="text-center text-blue-700">
                <Bell className="h-8 w-8 mx-auto mb-2" />
                <p className="font-medium">Notifications Active</p>
                <p className="text-sm">
                  You'll receive Telegram notifications when movies become available or new showtimes are added.
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Subscriptions;

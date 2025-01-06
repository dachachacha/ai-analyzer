import React, { createContext, useContext, useState } from 'react';

const StateContext = createContext();

export const StateProvider = ({ children }) => {
  const [queryState, setQueryState] = useState('');
  const [answerState, setAnswerState] = useState('');

  return (
    <StateContext.Provider value={{ queryState, setQueryState, answerState, setAnswerState }}>
      {children}
    </StateContext.Provider>
  );
};

export const useGlobalState = () => useContext(StateContext);

